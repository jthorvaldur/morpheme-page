#!/usr/bin/env node
// basis_rewriter.mjs -- Rewrite text for maximum basis_720 alignment
// Usage: node python/tools/basis_rewriter.mjs "your text here"
//        echo "your text" | node python/tools/basis_rewriter.mjs
// Self-contained, no external dependencies.

import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ---------------------------------------------------------------------------
// Load basis_720.json
// ---------------------------------------------------------------------------
const BASIS_PATH = resolve(__dirname, '../../data/basis_720.json');
let BASIS = {};
let BASIS_WORDS = new Set();

function loadBasis() {
  const raw = readFileSync(BASIS_PATH, 'utf-8');
  const data = JSON.parse(raw);
  data.forEach(entry => {
    const w = entry.word.toLowerCase();
    BASIS[w] = entry;
    BASIS_WORDS.add(w);
  });
}

// ---------------------------------------------------------------------------
// Normalize / lookup / tokenize  (mirrors viz/basis_filter.html logic)
// ---------------------------------------------------------------------------
function normalize(word) {
  return word.toLowerCase().replace(/[^a-z'-]/g, '').replace(/^'+|'+$/g, '');
}

function lookupBasis(word) {
  const w = normalize(word);
  if (!w) return null;
  if (BASIS[w]) return BASIS[w];

  const variants = [w];
  if (w.endsWith('s') && w.length > 3) variants.push(w.slice(0, -1));
  if (w.endsWith('es') && w.length > 4) variants.push(w.slice(0, -2));
  if (w.endsWith('ing') && w.length > 5) {
    variants.push(w.slice(0, -3));
    variants.push(w.slice(0, -3) + 'e');
  }
  if (w.endsWith('ed') && w.length > 4) {
    variants.push(w.slice(0, -2));
    variants.push(w.slice(0, -1));
  }
  if (w.endsWith('ly') && w.length > 4) variants.push(w.slice(0, -2));

  for (const v of variants) {
    if (BASIS[v]) return BASIS[v];
  }
  return null;
}

function tokenize(text) {
  const tokens = [];
  const re = /([a-zA-Z'-]+)|([^a-zA-Z'-]+)/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m[1]) {
      tokens.push({ type: 'word', raw: m[1], norm: normalize(m[1]) });
    } else {
      tokens.push({ type: 'punct', raw: m[2] });
    }
  }
  return tokens;
}

// ---------------------------------------------------------------------------
// SYNONYM_MAP  (extracted from viz/basis_filter.html)
// ---------------------------------------------------------------------------
const SYNONYM_MAP = {
  // ---- Pronouns / identity ----
  'i': 'man', 'me': 'man', 'myself': 'man',
  'we': 'person', 'us': 'person', 'ourselves': 'person',
  'you': 'person', 'yourself': 'person', 'yourselves': 'person',
  'he': 'man', 'him': 'man', 'himself': 'man',
  'she': 'woman', 'her': 'woman', 'herself': 'woman',
  'it': 'subject', 'itself': 'subject',
  'they': 'person', 'them': 'person', 'themselves': 'person',
  'who': 'person', 'whom': 'person', 'whose': 'person',
  'someone': 'person', 'somebody': 'person', 'anyone': 'person',
  'anybody': 'person', 'everyone': 'person', 'everybody': 'person',
  'nobody': 'person', 'none': 'person',

  // ---- Copula / linking (omit) ----
  'is': '', 'are': '', 'was': '', 'were': '', 'be': '',
  'been': '', 'being': '', 'am': '',

  // ---- Common verbs -> basis verbs ----
  'make': 'granting', 'makes': 'granting', 'made': 'granting', 'making': 'granting',
  'do': 'executing', 'does': 'executing', 'did': 'executing', 'doing': 'executing', 'done': 'executing',
  'create': 'granting', 'creates': 'granting', 'created': 'granting', 'creating': 'granting',
  'build': 'granting', 'builds': 'granting', 'built': 'granting', 'building': 'granting',
  'say': 'declaring', 'says': 'declaring', 'said': 'declaring', 'saying': 'declaring',
  'tell': 'communicating', 'tells': 'communicating', 'told': 'communicating', 'telling': 'communicating',
  'talk': 'communicating', 'talks': 'communicating', 'talked': 'communicating', 'talking': 'communicating',
  'speak': 'declaring', 'speaks': 'declaring', 'spoke': 'declaring', 'spoken': 'declaring', 'speaking': 'declaring',
  'want': 'claiming', 'wants': 'claiming', 'wanted': 'claiming', 'wanting': 'claiming',
  'need': 'requiring', 'needs': 'requiring', 'needed': 'requiring', 'needing': 'requiring',
  'go': 'moving', 'goes': 'moving', 'went': 'moving', 'going': 'moving', 'gone': 'moving',
  'come': 'appearing', 'comes': 'appearing', 'came': 'appearing', 'coming': 'appearing',
  'get': 'acquiring', 'gets': 'acquiring', 'got': 'acquiring', 'getting': 'acquiring', 'gotten': 'acquiring',
  'give': 'granting', 'gives': 'granting', 'gave': 'granting', 'given': 'granting', 'giving': 'granting',
  'take': 'seizing', 'takes': 'seizing', 'took': 'seizing', 'taken': 'seizing', 'taking': 'seizing',
  'know': 'informing', 'knows': 'informing', 'knew': 'informing', 'known': 'informing', 'knowing': 'informing',
  'think': 'adjudicating', 'thinks': 'adjudicating', 'thought': 'adjudicating', 'thinking': 'adjudicating',
  'see': 'disclosing', 'sees': 'disclosing', 'saw': 'disclosing', 'seen': 'disclosing', 'seeing': 'disclosing',
  'look': 'disclosing', 'looks': 'disclosing', 'looked': 'disclosing', 'looking': 'disclosing',
  'find': 'ruling', 'finds': 'ruling', 'found': 'ruling', 'finding': 'ruling',
  'put': 'filing', 'puts': 'filing', 'putting': 'filing',
  'use': 'executing', 'uses': 'executing', 'used': 'executing', 'using': 'executing',
  'try': 'prosecuting', 'tries': 'prosecuting', 'tried': 'prosecuting', 'trying': 'prosecuting',
  'ask': 'petitioning', 'asks': 'petitioning', 'asked': 'petitioning', 'asking': 'petitioning',
  'help': 'advising', 'helps': 'advising', 'helped': 'advising', 'helping': 'advising',
  'show': 'disclosing', 'shows': 'disclosing', 'showed': 'disclosing', 'shown': 'disclosing', 'showing': 'disclosing',
  'send': 'serving', 'sends': 'serving', 'sent': 'serving', 'sending': 'serving',
  'keep': 'securing', 'keeps': 'securing', 'kept': 'securing', 'keeping': 'securing',
  'let': 'permitting', 'lets': 'permitting', 'letting': 'permitting',
  'begin': 'filing', 'begins': 'filing', 'began': 'filing', 'begun': 'filing', 'beginning': 'filing',
  'start': 'filing', 'starts': 'filing', 'started': 'filing', 'starting': 'filing',
  'stop': 'restraining', 'stops': 'restraining', 'stopped': 'restraining', 'stopping': 'restraining',
  'end': 'dissolving', 'ends': 'dissolving', 'ended': 'dissolving', 'ending': 'dissolving',
  'run': 'governing', 'runs': 'governing', 'ran': 'governing', 'running': 'governing',
  'write': 'recording', 'writes': 'recording', 'wrote': 'recording', 'written': 'recording', 'writing': 'recording',
  'read': 'disclosing', 'reads': 'disclosing', 'reading': 'disclosing',
  'call': 'declaring', 'calls': 'declaring', 'called': 'declaring', 'calling': 'declaring',
  'move': 'moving', 'moves': 'moving', 'moved': 'moving',
  'live': 'standing', 'lives': 'standing', 'lived': 'standing',
  'die': 'death', 'dies': 'death', 'died': 'death', 'dying': 'death',
  'kill': 'harming', 'kills': 'harming', 'killed': 'harming', 'killing': 'harming',
  'hurt': 'harming', 'hurts': 'harming', 'hurting': 'harming',
  'cut': 'divesting', 'cuts': 'divesting', 'cutting': 'divesting',
  'hold': 'securing', 'holds': 'securing', 'held': 'securing', 'holding': 'securing',
  'stand': 'standing', 'stands': 'standing', 'stood': 'standing',
  'pay': 'paying', 'pays': 'paying', 'paid': 'paying',
  'meet': 'appearing', 'meets': 'appearing', 'met': 'appearing', 'meeting': 'appearing',
  'play': 'executing', 'plays': 'executing', 'played': 'executing', 'playing': 'executing',
  'turn': 'directing', 'turns': 'directing', 'turned': 'directing', 'turning': 'directing',
  'leave': 'releasing', 'leaves': 'releasing', 'left': 'releasing', 'leaving': 'releasing',
  'close': 'settling', 'closes': 'settling', 'closed': 'settling', 'closing': 'settling',
  'open': 'disclosing', 'opens': 'disclosing', 'opened': 'disclosing', 'opening': 'disclosing',
  'win': 'acquitting', 'wins': 'acquitting', 'won': 'acquitting', 'winning': 'acquitting',
  'lose': 'losing', 'lost': 'losing',
  'follow': 'enforcing', 'follows': 'enforcing', 'followed': 'enforcing', 'following': 'enforcing',
  'bring': 'conveying', 'brings': 'conveying', 'brought': 'conveying', 'bringing': 'conveying',
  'set': 'ordering', 'sets': 'ordering', 'setting': 'ordering',
  'lead': 'directing', 'leads': 'directing', 'led': 'directing', 'leading': 'directing',
  'understand': 'informing', 'understands': 'informing', 'understood': 'informing', 'understanding': 'informing',
  'allow': 'permitting', 'allows': 'permitting', 'allowed': 'permitting', 'allowing': 'permitting',
  'add': 'supplementing', 'adds': 'supplementing', 'added': 'supplementing', 'adding': 'supplementing',
  'grow': 'investing', 'grows': 'investing', 'grew': 'investing', 'grown': 'investing', 'growing': 'investing',
  'learn': 'informing', 'learns': 'informing', 'learned': 'informing', 'learning': 'informing',
  'change': 'amending', 'changes': 'amending', 'changed': 'amending', 'changing': 'amending',
  'watch': 'disclosing', 'watches': 'disclosing', 'watched': 'disclosing', 'watching': 'disclosing',
  'consider': 'adjudicating', 'considers': 'adjudicating', 'considered': 'adjudicating', 'considering': 'adjudicating',
  'believe': 'declaring', 'believes': 'declaring', 'believed': 'declaring', 'believing': 'declaring',
  'happen': 'appearing', 'happens': 'appearing', 'happened': 'appearing', 'happening': 'appearing',
  'include': 'incorporating', 'includes': 'incorporating', 'included': 'incorporating', 'including': 'incorporating',
  'continue': 'sustaining', 'continues': 'sustaining', 'continued': 'sustaining', 'continuing': 'sustaining',
  'offer': 'granting', 'offers': 'granting', 'offered': 'granting', 'offering': 'granting',
  'decide': 'ruling', 'decides': 'ruling', 'decided': 'ruling', 'deciding': 'ruling',
  'agree': 'agreeing', 'agrees': 'agreeing', 'agreed': 'agreeing',
  'expect': 'requiring', 'expects': 'requiring', 'expected': 'requiring', 'expecting': 'requiring',
  'mean': 'declaring', 'means': 'declaring', 'meant': 'declaring', 'meaning': 'declaring',
  'become': 'acquiring', 'becomes': 'acquiring', 'became': 'acquiring', 'becoming': 'acquiring',
  'remain': 'standing', 'remains': 'standing', 'remained': 'standing', 'remaining': 'standing',
  'suggest': 'advising', 'suggests': 'advising', 'suggested': 'advising', 'suggesting': 'advising',
  'raise': 'filing', 'raises': 'filing', 'raised': 'filing', 'raising': 'filing',
  'pass': 'conveying', 'passes': 'conveying', 'passed': 'conveying', 'passing': 'conveying',
  'sell': 'selling', 'sells': 'selling', 'sold': 'selling',
  'require': 'requiring', 'requires': 'requiring', 'required': 'requiring',
  'report': 'recording', 'reports': 'recording', 'reported': 'recording', 'reporting': 'recording',
  'describe': 'declaring', 'describes': 'declaring', 'described': 'declaring', 'describing': 'declaring',
  'develop': 'investing', 'develops': 'investing', 'developed': 'investing', 'developing': 'investing',
  'remove': 'divesting', 'removes': 'divesting', 'removed': 'divesting', 'removing': 'divesting',
  'prevent': 'restraining', 'prevents': 'restraining', 'prevented': 'restraining', 'preventing': 'restraining',
  'accept': 'confirming', 'accepts': 'confirming', 'accepted': 'confirming', 'accepting': 'confirming',
  'control': 'governing', 'controls': 'governing', 'controlled': 'governing', 'controlling': 'governing',
  'share': 'distributing', 'shares': 'distributing', 'shared': 'distributing', 'sharing': 'distributing',
  'protect': 'securing', 'protects': 'securing', 'protected': 'securing', 'protecting': 'securing',
  'choose': 'ruling', 'chooses': 'ruling', 'chose': 'ruling', 'chosen': 'ruling', 'choosing': 'ruling',
  'pick': 'seizing', 'picks': 'seizing', 'picked': 'seizing', 'picking': 'seizing',
  'fight': 'prosecuting', 'fights': 'prosecuting', 'fought': 'prosecuting', 'fighting': 'prosecuting',
  'force': 'compelling', 'forces': 'compelling', 'forced': 'compelling', 'forcing': 'compelling',
  'break': 'breaching', 'breaks': 'breaching', 'broke': 'breaching', 'broken': 'breaching', 'breaking': 'breaching',
  'destroy': 'annulling', 'destroys': 'annulling', 'destroyed': 'annulling', 'destroying': 'annulling',
  'fix': 'amending', 'fixes': 'amending', 'fixed': 'amending', 'fixing': 'amending',
  'place': 'filing', 'places': 'filing', 'placed': 'filing', 'placing': 'filing',
  'join': 'merging', 'joins': 'merging', 'joined': 'merging', 'joining': 'merging',
  'sign': 'certifying', 'signs': 'certifying', 'signed': 'certifying', 'signing': 'certifying',
  'check': 'assessing', 'checks': 'assessing', 'checked': 'assessing', 'checking': 'assessing',
  'own': 'own', 'owns': 'securing', 'owned': 'securing', 'owning': 'securing',
  'belong': 'inheriting', 'belongs': 'inheriting', 'belonged': 'inheriting', 'belonging': 'inheriting',
  'deny': 'objecting', 'denies': 'objecting', 'denied': 'objecting', 'denying': 'objecting',
  'refuse': 'objecting', 'refuses': 'objecting', 'refused': 'objecting', 'refusing': 'objecting',
  'forbid': 'prohibiting', 'forbids': 'prohibiting', 'forbade': 'prohibiting', 'forbidden': 'prohibiting',
  'ban': 'prohibiting', 'bans': 'prohibiting', 'banned': 'prohibiting', 'banning': 'prohibiting',
  'promise': 'agreeing', 'promises': 'agreeing', 'promised': 'agreeing', 'promising': 'agreeing',
  'prove': 'certifying', 'proves': 'certifying', 'proved': 'certifying', 'proven': 'certifying', 'proving': 'certifying',
  'demand': 'requiring', 'demands': 'requiring', 'demanded': 'requiring', 'demanding': 'requiring',
  'claim': 'claiming', 'claims': 'claiming', 'claimed': 'claiming',
  'announce': 'declaring', 'announces': 'declaring', 'announced': 'declaring', 'announcing': 'declaring',
  'assign': 'assigning', 'assigns': 'assigning', 'assigned': 'assigning',
  'buy': 'purchasing', 'buys': 'purchasing', 'bought': 'purchasing', 'buying': 'purchasing',
  'enter': 'filing', 'enters': 'filing', 'entered': 'filing', 'entering': 'filing',
  'exist': 'standing', 'exists': 'standing', 'existed': 'standing', 'existing': 'standing',
  'appear': 'appearing', 'appears': 'appearing', 'appeared': 'appearing',
  'serve': 'serving', 'serves': 'serving', 'served': 'serving',
  'manage': 'managing', 'manages': 'managing', 'managed': 'managing',
  'produce': 'executing', 'produces': 'executing', 'produced': 'executing', 'producing': 'executing',
  'receive': 'acquiring', 'receives': 'acquiring', 'received': 'acquiring', 'receiving': 'acquiring',
  'represent': 'representing', 'represents': 'representing', 'represented': 'representing',
  'support': 'sustaining', 'supports': 'sustaining', 'supported': 'sustaining', 'supporting': 'sustaining',
  'publish': 'publishing', 'publishes': 'publishing', 'published': 'publishing',
  'reach': 'settling', 'reaches': 'settling', 'reached': 'settling', 'reaching': 'settling',
  'apply': 'enforcing', 'applies': 'enforcing', 'applied': 'enforcing', 'applying': 'enforcing',
  'transfer': 'transferring', 'transfers': 'transferring', 'transferred': 'transferring',
  'return': 'releasing', 'returns': 'releasing', 'returned': 'releasing', 'returning': 'releasing',
  'replace': 'replacing', 'replaces': 'replacing', 'replaced': 'replacing',
  'save': 'securing', 'saves': 'securing', 'saved': 'securing', 'saving': 'securing',
  'spend': 'paying', 'spends': 'paying', 'spent': 'paying', 'spending': 'paying',
  'point': 'directing', 'points': 'directing', 'pointed': 'directing', 'pointing': 'directing',
  'push': 'compelling', 'pushes': 'compelling', 'pushed': 'compelling', 'pushing': 'compelling',
  'pull': 'seizing', 'pulls': 'seizing', 'pulled': 'seizing', 'pulling': 'seizing',

  // ---- Common nouns -> basis nouns ----
  'thing': 'property', 'things': 'property', 'stuff': 'property', 'object': 'instrument',
  'objects': 'instrument', 'item': 'instrument', 'items': 'instrument',
  'money': 'currency', 'cash': 'capital', 'dollar': 'currency', 'dollars': 'currency',
  'price': 'value', 'cost': 'fee', 'costs': 'fee',
  'work': 'commerce', 'job': 'trade', 'jobs': 'trade', 'career': 'commerce',
  'business': 'commerce', 'company': 'company', 'companies': 'company',
  'home': 'estate', 'house': 'estate', 'houses': 'estate', 'apartment': 'estate',
  'country': 'sovereignty', 'nation': 'sovereignty', 'state': 'jurisdiction',
  'city': 'jurisdiction', 'town': 'jurisdiction', 'government': 'authority',
  'people': 'person', 'human': 'person', 'humans': 'person', 'individual': 'person', 'individuals': 'person',
  'children': 'child', 'baby': 'child', 'kid': 'child', 'kids': 'child',
  'father': 'man', 'mother': 'woman', 'parent': 'guardian', 'parents': 'guardian',
  'brother': 'man', 'sister': 'woman', 'family': 'estate', 'husband': 'man', 'wife': 'woman',
  'friend': 'person', 'friends': 'person', 'enemy': 'defendant',
  'teacher': 'counsel', 'student': 'ward', 'students': 'ward', 'school': 'institute',
  'doctor': 'counsel', 'hospital': 'institute',
  'police': 'authority', 'officer': 'administrator', 'soldier': 'person',
  'queen': 'woman', 'lord': 'grantor', 'master': 'administrator',
  'idea': 'claim', 'ideas': 'claim', 'concept': 'clause', 'thought': 'opinion',
  'story': 'record', 'stories': 'record', 'book': 'codex', 'books': 'codex',
  'letter': 'document', 'letters': 'document', 'message': 'notice',
  'question': 'petition', 'questions': 'petition', 'answer': 'verdict',
  'problem': 'complaint', 'problems': 'complaint', 'issue': 'claim', 'issues': 'claim',
  'reason': 'fact', 'reasons': 'fact', 'cause': 'claim', 'result': 'judgment',
  'way': 'instrument', 'ways': 'instrument', 'method': 'instrument',
  'strength': 'power', 'ability': 'power',
  'rights': 'right',
  'truth': 'fact', 'facts': 'fact', 'lie': 'fraud',
  'laws': 'law', 'rule': 'regulation', 'rules': 'regulation',
  'crime': 'conviction', 'punishment': 'penalty', 'prison': 'imprisonment', 'jail': 'imprisonment',
  'car': 'vessel', 'vehicle': 'vessel', 'boat': 'vessel', 'plane': 'vessel',
  'food': 'property', 'earth': 'land', 'ground': 'soil',
  'sky': 'jurisdiction', 'air': 'spirit', 'fire': 'forfeiture', 'light': 'evidence',
  'world': 'dominion', 'universe': 'dominion', 'nature': 'dominion',
  'life': 'liberty',
  'words': 'word',
  'picture': 'instrument', 'image': 'seal', 'symbol': 'seal',
  'music': 'sound', 'song': 'sound',
  'door': 'bar', 'window': 'bar', 'wall': 'bar',
  'paper': 'document', 'documents': 'document',
  'form': 'instrument',
  'plan': 'motion', 'goal': 'claim', 'target': 'subject',
  'group': 'association', 'team': 'association', 'organization': 'corporation',
  'market': 'exchange', 'store': 'registry', 'shop': 'commerce',
  'system': 'code', 'process': 'motion', 'part': 'clause', 'parts': 'clause',
  'type': 'code', 'kind': 'code', 'sort': 'code', 'class': 'code',
  'example': 'evidence', 'test': 'assessment', 'trial': 'tribunal',
  'number': 'account', 'amount': 'value', 'total': 'account',
  'level': 'jurisdiction',
  'line': 'bar', 'side': 'jurisdiction',
  'age': 'statute', 'time': 'sentence', 'year': 'sentence', 'years': 'sentence',
  'day': 'sentence', 'days': 'sentence', 'week': 'sentence', 'month': 'sentence',
  'night': 'sentence', 'morning': 'sentence', 'evening': 'sentence',
  'war': 'motion', 'peace': 'agreement', 'battle': 'motion',
  'god': 'authority', 'church': 'institute', 'religion': 'canon',
  'taxes': 'tax', 'debt': 'liability', 'debts': 'liability',
  'loan': 'mortgage', 'interest': 'premium', 'profit': 'revenue',
  'loss': 'forfeiture',
  'street': 'venue', 'road': 'venue', 'path': 'venue',
  'garden': 'land', 'park': 'land', 'field': 'land',
  'ocean': 'sea', 'river': 'canal', 'lake': 'water',
  'tree': 'property', 'flower': 'property', 'animal': 'chattel',
  'dog': 'chattel', 'horse': 'chattel', 'fish': 'chattel', 'bird': 'chattel',
  'color': 'property', 'colour': 'property', 'shape': 'instrument',
  'size': 'value', 'weight': 'value', 'measure': 'assessment',
  'email': 'notice', 'phone': 'instrument', 'computer': 'instrument',
  'internet': 'exchange', 'website': 'registry', 'page': 'document',
  'content': 'record', 'information': 'evidence', 'data': 'evidence',
  'news': 'notice',
  'text': 'record', 'list': 'register',
  'film': 'record', 'movie': 'record', 'game': 'motion',
  'sport': 'commerce', 'race': 'motion',
  'dress': 'property', 'clothes': 'property', 'shoe': 'chattel', 'hat': 'chattel',
  'tool': 'instrument', 'machine': 'instrument', 'weapon': 'instrument',
  'gift': 'compensation', 'reward': 'compensation', 'prize': 'compensation',
  'attention': 'notice', 'focus': 'motion',
  'views': 'opinion', 'belief': 'claim',
  'place': 'venue', 'places': 'venue', 'area': 'jurisdiction', 'areas': 'jurisdiction',
  'girl': 'woman', 'boy': 'man', 'guy': 'man', 'guys': 'person',
  'mr': 'man', 'mrs': 'woman', 'miss': 'woman', 'sir': 'man',
  'lady': 'woman', 'gentleman': 'man',
  'act': 'statute', 'action': 'motion', 'activity': 'commerce',
  'situation': 'motion', 'condition': 'clause', 'conditions': 'clause',
  'case': 'claim', 'cases': 'claim',
  'sense': 'opinion', 'feeling': 'opinion', 'feelings': 'opinion',
  'experience': 'evidence',
  'knowledge': 'evidence', 'education': 'institute',
  'science': 'evidence', 'research': 'assessment',
  'technology': 'instrument', 'art': 'instrument',
  'service': 'commerce', 'services': 'commerce',
  'product': 'property', 'products': 'property',
  'model': 'instrument', 'design': 'instrument',
  'analysis': 'assessment', 'performance': 'execution',

  // ---- Common adjectives -> basis adjectives ----
  'good': 'lawful', 'great': 'sovereign', 'nice': 'beneficial',
  'bad': 'fraudulent', 'terrible': 'invalid', 'awful': 'invalid', 'horrible': 'criminal',
  'big': 'substantial', 'large': 'substantial', 'huge': 'absolute', 'enormous': 'absolute',
  'small': 'nominal', 'little': 'nominal', 'tiny': 'nominal', 'minor': 'inferior',
  'new': 'current', 'old': 'ancient', 'young': 'living', 'modern': 'modern',
  'long': 'perpetual', 'short': 'temporary', 'tall': 'superior', 'high': 'superior',
  'low': 'inferior', 'deep': 'fundamental',
  'important': 'material', 'main': 'primary', 'key': 'primary', 'major': 'primary',
  'real': 'real', 'true': 'correct', 'false': 'fraudulent', 'fake': 'fictitious',
  'wrong': 'incorrect',
  'hard': 'binding', 'soft': 'equitable', 'strong': 'sovereign', 'weak': 'inferior',
  'fast': 'express', 'slow': 'provisional', 'quick': 'express', 'rapid': 'express',
  'early': 'prior', 'late': 'subsequent',
  'full': 'absolute', 'empty': 'null', 'complete': 'absolute',
  'open': 'public', 'closed': 'private', 'free': 'sovereign', 'clear': 'apparent',
  'dark': 'constructive', 'bright': 'apparent',
  'hot': 'express', 'cold': 'constructive', 'warm': 'equitable', 'cool': 'equitable',
  'rich': 'beneficial', 'poor': 'pecuniary', 'wealthy': 'proprietary',
  'safe': 'secured', 'dangerous': 'criminal', 'secure': 'secured',
  'happy': 'beneficial', 'sad': 'penal', 'angry': 'punitive',
  'beautiful': 'sovereign', 'ugly': 'invalid', 'pretty': 'equitable',
  'easy': 'express', 'difficult': 'constructive', 'simple': 'nominal', 'complex': 'constructive',
  'different': 'indirect', 'similar': 'common',
  'special': 'proprietary', 'general': 'common', 'specific': 'express',
  'political': 'constitutional', 'social': 'civil', 'economic': 'commercial',
  'national': 'domestic', 'international': 'foreign', 'local': 'municipal',
  'physical': 'tangible', 'mental': 'constructive',
  'possible': 'conditional', 'impossible': 'invalid',
  'sure': 'absolute', 'likely': 'presumptive', 'unlikely': 'conditional',
  'ready': 'operative', 'available': 'current', 'present': 'current',
  'past': 'prior', 'future': 'subsequent', 'recent': 'current',
  'final': 'absolute',
  'alive': 'living', 'sick': 'penal', 'healthy': 'living',
  'guilty': 'criminal', 'innocent': 'lawful',
  'amazing': 'sovereign', 'awesome': 'sovereign', 'incredible': 'absolute',
  'wonderful': 'beneficial', 'perfect': 'absolute', 'excellent': 'superior',
  'crazy': 'invalid', 'insane': 'invalid', 'wild': 'fraudulent',
  'cute': 'equitable', 'lovely': 'beneficial',
  'basic': 'fundamental', 'ordinary': 'common', 'normal': 'common', 'standard': 'statutory',
  'extra': 'nominal',
  'holy': 'canonical', 'sacred': 'ecclesiastical', 'divine': 'canonical',
  'legal': 'legal', 'illegal': 'criminal', 'official': 'statutory',
  'independent': 'sovereign', 'separate': 'indirect',

  // ---- Common adverbs -> basis adverbs ----
  'very': 'absolutely', 'really': 'actually', 'truly': 'actually',
  'just': 'presently', 'only': 'exclusively', 'also': 'additionally',
  'too': 'additionally', 'already': 'previously', 'still': 'presently',
  'yet': 'presently', 'even': 'inclusively', 'quite': 'substantially',
  'almost': 'partially', 'maybe': 'conditionally',
  'perhaps': 'conditionally', 'probably': 'presumptively', 'possibly': 'conditionally',
  'certainly': 'absolutely', 'definitely': 'absolutely', 'surely': 'absolutely',
  'obviously': 'expressly', 'clearly': 'expressly',
  'basically': 'generally', 'exactly': 'specifically', 'especially': 'particularly',
  'usually': 'generally', 'sometimes': 'seldom',
  'again': 'subsequently',
  'together': 'jointly', 'alone': 'severally', 'apart': 'severally',
  'here': 'herein', 'there': 'therein', 'somewhere': 'therein', 'everywhere': 'wholly',
  'soon': 'forthwith', 'later': 'thereafter',
  'today': 'presently', 'tomorrow': 'hereafter', 'yesterday': 'previously',
  'recently': 'previously', 'suddenly': 'forthwith',
  'slowly': 'provisionally', 'quickly': 'promptly',
  'well': 'properly', 'badly': 'negligently',
  'carefully': 'duly', 'directly': 'expressly', 'simply': 'nominally',
  'partly': 'partially', 'mostly': 'substantially',
  'however': 'nevertheless', 'instead': 'alternatively', 'meanwhile': 'simultaneously',
  'literally': 'expressly', 'honestly': 'lawfully', 'seriously': 'materially',
  'apparently': 'presumptively', 'unfortunately': 'consequently',
  'so': 'accordingly', 'okay': 'duly',

  // ---- Filler / function words ----
  'not': 'without', "n't": 'without', 'dont': 'without', "don't": 'without',
  'can': '', 'could': '', 'will': '', 'would': '', 'shall': '',
  'should': '', 'may': '', 'might': '', 'must': '',
  'has': '', 'have': '', 'had': '', 'having': '',
  'what': 'subject', 'which': 'subject', 'where': 'venue',
  'when': 'sentence', 'why': 'claim', 'how': 'instrument',
  'if': 'conditionally', 'but': 'notwithstanding', 'because': 'therefore',
  'while': 'during', 'although': 'notwithstanding',
  'though': 'notwithstanding', 'unless': 'without',
  'and': '', 'or': 'alternatively', 'nor': 'neither',
  'than': 'versus', 'as': 'per',
  'whether': 'conditionally',
  'rather': 'alternatively',
};

// ---------------------------------------------------------------------------
// Rewrite engine  (mirrors viz/basis_filter.html logic)
// ---------------------------------------------------------------------------
function rewriteWord(word) {
  const w = normalize(word);
  if (!w) return { original: word, replacement: '', action: 'punct' };

  // Already in basis
  if (lookupBasis(w)) {
    return { original: word, replacement: w, action: 'keep' };
  }

  // Check synonym map
  if (SYNONYM_MAP[w] !== undefined) {
    const mapped = SYNONYM_MAP[w];
    if (mapped === '') {
      return { original: word, replacement: '', action: 'drop' };
    }
    return { original: word, replacement: mapped, action: 'substitute' };
  }

  // Morphological fallback: suffix-based matching
  if (w.endsWith('tion') || w.endsWith('sion')) {
    const stem = w.replace(/[ts]ion$/, '');
    for (const bw of BASIS_WORDS) {
      if (bw.startsWith(stem.slice(0, Math.min(4, stem.length))) && BASIS[bw].role === 'noun') {
        return { original: word, replacement: bw, action: 'substitute' };
      }
    }
  }

  if (w.endsWith('ment')) {
    const stem = w.replace(/ment$/, '');
    for (const bw of BASIS_WORDS) {
      if (bw.startsWith(stem.slice(0, Math.min(4, stem.length))) && BASIS[bw].role === 'noun') {
        return { original: word, replacement: bw, action: 'substitute' };
      }
    }
  }

  if (w.endsWith('ness')) {
    const stem = w.replace(/ness$/, '');
    if (lookupBasis(stem)) {
      return { original: word, replacement: stem, action: 'substitute' };
    }
  }

  if ((w.endsWith('er') || w.endsWith('or')) && w.length > 4) {
    const stem = w.slice(0, -2);
    for (const bw of BASIS_WORDS) {
      if (bw.startsWith(stem.slice(0, Math.min(3, stem.length))) && (BASIS[bw].role === 'noun' || BASIS[bw].role === 'verb')) {
        return { original: word, replacement: bw, action: 'substitute' };
      }
    }
  }

  if (w.endsWith('able') || w.endsWith('ible')) {
    const stem = w.replace(/[ai]ble$/, '');
    for (const bw of BASIS_WORDS) {
      if (bw.startsWith(stem.slice(0, Math.min(3, stem.length))) && BASIS[bw].role === 'adjective') {
        return { original: word, replacement: bw, action: 'substitute' };
      }
    }
  }

  // No match
  return { original: word, replacement: '', action: 'nomatch' };
}

function basisRewrite(text) {
  const tokens = tokenize(text);
  const changelog = [];
  const rewritten = [];

  tokens.forEach(t => {
    if (t.type === 'punct') {
      rewritten.push({ raw: t.raw, type: 'punct' });
      return;
    }
    const result = rewriteWord(t.raw);
    if (result.action === 'keep') {
      rewritten.push({ raw: result.replacement, type: 'kept', original: t.raw });
    } else if (result.action === 'substitute') {
      rewritten.push({ raw: result.replacement, type: 'changed', original: t.raw });
      changelog.push({ from: t.raw, to: result.replacement, action: 'substituted' });
    } else if (result.action === 'drop') {
      rewritten.push({ raw: '', type: 'dropped', original: t.raw });
      changelog.push({ from: t.raw, to: '(dropped)', action: 'dropped' });
    } else {
      rewritten.push({ raw: '', type: 'nomatch', original: t.raw });
      changelog.push({ from: t.raw, to: '(no equivalent)', action: 'nomatch' });
    }
  });

  return { rewritten, changelog };
}

// ---------------------------------------------------------------------------
// Coverage computation
// ---------------------------------------------------------------------------
function computeCoverage(text) {
  const tokens = tokenize(text);
  const words = tokens.filter(t => t.type === 'word' && t.norm.length > 0);
  if (words.length === 0) return { total: 0, basis: 0, pct: 0 };
  const basis = words.filter(t => lookupBasis(t.norm)).length;
  return { total: words.length, basis, pct: basis / words.length };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  loadBasis();

  // Get input text: CLI argument or stdin
  let text = '';
  const args = process.argv.slice(2);

  if (args.length > 0) {
    text = args.join(' ');
  } else {
    // Read from stdin
    const chunks = [];
    process.stdin.setEncoding('utf-8');
    for await (const chunk of process.stdin) {
      chunks.push(chunk);
    }
    text = chunks.join('').trim();
  }

  if (!text) {
    console.error('Usage: node python/tools/basis_rewriter.mjs "your text here"');
    console.error('       echo "your text" | node python/tools/basis_rewriter.mjs');
    process.exit(1);
  }

  // Compute original coverage
  const origCoverage = computeCoverage(text);

  // Rewrite
  const result = basisRewrite(text);
  const parts = [];
  result.rewritten.forEach(r => {
    if (r.type === 'punct') parts.push(r.raw);
    else if (r.raw) parts.push(r.raw);
  });
  const rewrittenText = parts.join('').replace(/\s+/g, ' ').trim();

  // Compute new coverage
  const newCoverage = computeCoverage(rewrittenText);

  // Changelog summary
  const substituted = result.changelog.filter(c => c.action === 'substituted');
  const dropped = result.changelog.filter(c => c.action === 'dropped');
  const noMatch = result.changelog.filter(c => c.action === 'nomatch');

  // Output
  const SEP = '─'.repeat(60);

  console.log();
  console.log(SEP);
  console.log('  BASIS REWRITER -- Maximize basis_720 alignment');
  console.log(SEP);

  console.log();
  console.log('ORIGINAL:');
  console.log(`  ${text}`);

  console.log();
  console.log('REWRITTEN:');
  console.log(`  ${rewrittenText}`);

  console.log();
  console.log(SEP);
  console.log('COVERAGE');
  console.log(SEP);
  console.log(`  Before:  ${origCoverage.basis}/${origCoverage.total} words in basis (${(origCoverage.pct * 100).toFixed(1)}%)`);
  console.log(`  After:   ${newCoverage.basis}/${newCoverage.total} words in basis (${(newCoverage.pct * 100).toFixed(1)}%)`);
  const delta = newCoverage.pct - origCoverage.pct;
  const deltaSign = delta >= 0 ? '+' : '';
  console.log(`  Change:  ${deltaSign}${(delta * 100).toFixed(1)} percentage points`);

  console.log();
  console.log(SEP);
  console.log(`CHANGELOG  (${result.changelog.length} changes)`);
  console.log(SEP);

  if (substituted.length > 0) {
    console.log();
    console.log(`  Substituted (${substituted.length}):`);
    substituted.forEach(c => {
      console.log(`    ${c.from} -> ${c.to}`);
    });
  }

  if (dropped.length > 0) {
    console.log();
    console.log(`  Dropped (${dropped.length}):`);
    dropped.forEach(c => {
      console.log(`    ${c.from}`);
    });
  }

  if (noMatch.length > 0) {
    console.log();
    console.log(`  No equivalent (${noMatch.length}):`);
    noMatch.forEach(c => {
      console.log(`    ${c.from}`);
    });
  }

  console.log();
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
