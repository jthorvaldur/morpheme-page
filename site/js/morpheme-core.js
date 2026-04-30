/**
 * morpheme-core.js — Shared morpheme data loader and analysis functions
 *
 * Single source of truth: /data/morphemes.json (exported from Python)
 * All viz pages should use this module instead of hardcoding dictionaries.
 *
 * Usage:
 *   <script src="/js/morpheme-core.js"></script>
 *   <script>
 *     MorphemeCore.load().then(() => {
 *       const info = MorphemeCore.getInfo('jurisdiction');
 *       const decomp = MorphemeCore.decompose('insurance');
 *     });
 *   </script>
 */

const MorphemeCore = (function() {
  'use strict';

  // State
  let loaded = false;
  let PREFIXES = {};
  let ROOTS = {};
  let SUFFIXES = {};
  let VCC_NEGATION = {};
  let DECOMPOSITIONS = {};
  let WORD_RANKS = {};
  let SYNONYM_MAP = {};
  let BASIS = {};

  // Sorted keys for longest-match-first
  let PREFIXES_SORTED = [];
  let ROOTS_SORTED = [];
  let SUFFIXES_SORTED = [];

  // Stop words
  const STOPS = new Set(
    'the a an is are was were be been being have has had do does did will would could should shall may might can to of in for on at by with from as into through during before after above below between and but or nor so yet not no it its this that these those i me my you your he him his she her we us our they them their than very just also too then now here there when where how what which who if because although while since until unless however therefore really basically literally actually like oh ok okay omg um uh well yeah yes right'.split(' ')
  );

  /**
   * Load morpheme data from /data/morphemes.json and /data/basis_720.json
   */
  async function load() {
    if (loaded) return;

    try {
      const [morphRes, basisRes] = await Promise.all([
        fetch('/data/morphemes.json'),
        fetch('/data/basis_720.json'),
      ]);

      if (morphRes.ok) {
        const data = await morphRes.json();
        PREFIXES = data.prefixes || {};
        ROOTS = data.roots || {};
        SUFFIXES = data.suffixes || {};
        VCC_NEGATION = data.vcc_negation_prefixes || {};
        DECOMPOSITIONS = data.known_decompositions || {};
        WORD_RANKS = data.word_frequency_ranks || {};
        SYNONYM_MAP = data.synonym_map || {};

        PREFIXES_SORTED = Object.keys(PREFIXES).sort((a,b) => b.length - a.length);
        ROOTS_SORTED = Object.keys(ROOTS).sort((a,b) => b.length - a.length);
        SUFFIXES_SORTED = Object.keys(SUFFIXES).sort((a,b) => b.length - a.length);
      }

      if (basisRes.ok) {
        const basisData = await basisRes.json();
        basisData.forEach(function(e) { BASIS[e.word.toLowerCase()] = e; });
      }

      loaded = true;
    } catch(e) {
      console.warn('MorphemeCore: failed to load data files', e);
    }
  }

  /**
   * Information content of a word (Shannon surprisal in bits)
   */
  function getInfo(word) {
    var w = word.toLowerCase().replace(/[^a-z]/g, '');
    if (!w) return 0;
    var rank = WORD_RANKS[w];
    if (rank) return Math.log2(rank) + 2;
    return Math.min(10 + w.length * 0.5, 16);
  }

  /**
   * Is this a content word (not a stop word)?
   */
  function isContent(word) {
    var w = word.toLowerCase().replace(/[^a-z]/g, '');
    return !STOPS.has(w) && w.length > 2;
  }

  /**
   * Is this word in the basis_720?
   */
  function inBasis(word) {
    return BASIS[word.toLowerCase().replace(/[^a-z]/g, '')] || null;
  }

  /**
   * Find prefix in a word (longest match first)
   */
  function findPrefix(word) {
    for (var i = 0; i < PREFIXES_SORTED.length; i++) {
      var pfx = PREFIXES_SORTED[i];
      if (word.indexOf(pfx) === 0 && word.length > pfx.length + 1) {
        var rest = word.slice(pfx.length);
        if (rest.length >= 2) return { prefix: pfx, meaning: PREFIXES[pfx], remainder: rest };
      }
    }
    return null;
  }

  /**
   * Find suffix in a word (longest match first)
   */
  function findSuffix(word) {
    for (var i = 0; i < SUFFIXES_SORTED.length; i++) {
      var sfx = SUFFIXES_SORTED[i];
      if (word.length > sfx.length + 1 && word.indexOf(sfx, word.length - sfx.length) !== -1) {
        return { stem: word.slice(0, -sfx.length), suffix: sfx, meaning: SUFFIXES[sfx] };
      }
    }
    return { stem: word, suffix: '', meaning: '' };
  }

  /**
   * Find root in a stem
   */
  function findRoot(stem) {
    if (ROOTS[stem]) return { root: stem, meaning: ROOTS[stem] };
    for (var i = 0; i < ROOTS_SORTED.length; i++) {
      var r = ROOTS_SORTED[i];
      if (r.length >= 2 && stem.indexOf(r) === 0) return { root: r, meaning: ROOTS[r] };
    }
    for (var i = 0; i < ROOTS_SORTED.length; i++) {
      var r = ROOTS_SORTED[i];
      if (r.length >= 3 && stem.indexOf(r) !== -1) return { root: r, meaning: ROOTS[r] };
    }
    return { root: stem, meaning: '' };
  }

  /**
   * Full morphological decomposition
   */
  function decompose(word) {
    var w = word.toLowerCase().trim();
    if (DECOMPOSITIONS[w]) return Object.assign({}, DECOMPOSITIONS[w]);

    var prefix = '', prefixMeaning = '', remainder = w;
    var pfxResult = findPrefix(w);
    if (pfxResult) {
      prefix = pfxResult.prefix;
      prefixMeaning = pfxResult.meaning;
      remainder = pfxResult.remainder;
    }

    var sfxResult = findSuffix(remainder);
    var rootResult = findRoot(sfxResult.stem);
    var isNegated = prefix in VCC_NEGATION;

    var parts = [];
    if (prefixMeaning) parts.push(prefixMeaning.toUpperCase());
    if (rootResult.meaning) parts.push(rootResult.meaning);
    else parts.push(rootResult.root);
    if (sfxResult.meaning) parts.push('(' + sfxResult.meaning + ')');

    return {
      word: w,
      prefix: prefix,
      prefix_meaning: prefixMeaning,
      root: rootResult.root,
      root_meaning: rootResult.meaning,
      suffix: sfxResult.suffix,
      suffix_meaning: sfxResult.meaning,
      is_negated: isNegated,
      true_meaning: parts.join(' + '),
      apparent_meaning: '',
    };
  }

  /**
   * Analyze a block of text — returns coherence metrics
   */
  function analyzeText(text) {
    var words = text.toLowerCase().replace(/[^a-z' -]/g, ' ').split(/\s+/).filter(function(w) { return w.length > 0; });
    if (words.length === 0) return null;

    var infos = words.map(function(w) { return getInfo(w.replace(/[^a-z]/g, '')); });
    var totalInfo = infos.reduce(function(s,b) { return s+b; }, 0);
    var avgInfo = totalInfo / words.length;

    var unique = {};
    words.forEach(function(w) { unique[w.replace(/[^a-z]/g, '')] = 1; });
    var uniqueCount = Object.keys(unique).length;
    var vocabRichness = uniqueCount / words.length;

    var contentWords = words.filter(function(w) { return isContent(w); });
    var contentRatio = contentWords.length / words.length;

    var freq = {};
    words.forEach(function(w) { var c = w.replace(/[^a-z]/g, ''); freq[c] = (freq[c]||0)+1; });
    var redundancy = 1 - vocabRichness;

    var basisHits = 0, nouns = 0;
    words.forEach(function(w) {
      var b = inBasis(w);
      if (b) { basisHits++; if (b.role === 'noun') nouns++; }
    });

    var coherence = Math.min(100, Math.max(0,
      (avgInfo / 12) * 30 + contentRatio * 30 + vocabRichness * 25 + (1 - redundancy) * 15
    ));

    return {
      wordCount: words.length,
      totalInfo: totalInfo,
      avgInfo: avgInfo,
      uniqueCount: uniqueCount,
      vocabRichness: vocabRichness,
      contentWords: contentWords.length,
      contentRatio: contentRatio,
      redundancy: redundancy,
      basisHits: basisHits,
      basisCoverage: basisHits / words.length,
      nouns: nouns,
      coherence: coherence,
      freq: freq,
    };
  }

  // Public API
  return {
    load: load,
    getInfo: getInfo,
    isContent: isContent,
    inBasis: inBasis,
    findPrefix: findPrefix,
    findSuffix: findSuffix,
    findRoot: findRoot,
    decompose: decompose,
    analyzeText: analyzeText,
    isLoaded: function() { return loaded; },
    getStats: function() {
      return {
        prefixes: Object.keys(PREFIXES).length,
        roots: Object.keys(ROOTS).length,
        suffixes: Object.keys(SUFFIXES).length,
        basis: Object.keys(BASIS).length,
        ranks: Object.keys(WORD_RANKS).length,
        synonyms: Object.keys(SYNONYM_MAP).length,
      };
    },
    // Direct access for pages that need raw data
    data: {
      get prefixes() { return PREFIXES; },
      get roots() { return ROOTS; },
      get suffixes() { return SUFFIXES; },
      get vccNegation() { return VCC_NEGATION; },
      get decompositions() { return DECOMPOSITIONS; },
      get wordRanks() { return WORD_RANKS; },
      get synonymMap() { return SYNONYM_MAP; },
      get basis() { return BASIS; },
      get stops() { return STOPS; },
    },
  };
})();
