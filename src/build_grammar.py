"""Build per-word sarf (morphology) and nahw (iʿrāb) for the word card.

Inputs (in grammar/, not committed; see README for where to download them):
  quranic-corpus-morphology-0.4.txt   Quranic Arabic Corpus 0.4 (corpus.quran.com): root, lemma, verb form, aspect, voice, person
  MASAQ.csv                           MASAQ dataset (CC BY 4.0, doi:10.17632/9yvrzxktmr.5): iʿrāb role, case, case marker
Output: src/grammar.json = {"s": [strings…], "q": {sūrah: [[word, …] per āyah]}}
Each word is a flat list of indices into "s":
  [type, typeKey, root, rootClass, bab, wazn, person, roleKey, lemma, meaningRu, meaningKk, segment, iʿrāb, segment, iʿrāb, …]
The two meanings come from lemma_meanings.txt (automatic translation of the commonest dictionary entries).
"""
import csv, json, os, re, sys
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lemmas  # dictionary entries and their ranks

SRC = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(os.path.dirname(SRC), "grammar")

BW = dict(zip("'|><&}AbptvjHxd*rzs$SDTZEg_fqklmnhwYyFNKaui~o^#`{",
              "ءآأإؤئابةتثجحخدذرزسشصضطظعغـ"
              "فقكلمنهوىيًٌٍَُِّْٰٓٔٱ"))  # Buckwalter -> Arabic
def ar(bw): return "".join(BW.get(c, "") for c in bw)

HARAKAT = "ًٌٍَُِّْ"
MARKS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ࣓-ࣿـ]")
HAMZA = set("ءأإؤئآ")

# ---------------------------------------------------------------- strings table
strings, index = [""], {"": 0}
def S(text):
    if text not in index:
        index[text] = len(strings); strings.append(text)
    return index[text]

# ---------------------------------------------------------------- sarf
TYPE = {  # corpus part of speech -> (Arabic label, gloss key)
    "N": ("اسم", "noun"), "PN": ("اسم علم", "propn"), "ADJ": ("صفة", "adj"), "PRON": ("ضمير", "pron"),
    "DEM": ("اسم إشارة", "dem"), "REL": ("اسم موصول", "rel"), "T": ("ظرف زمان", "advt"), "LOC": ("ظرف مكان", "advp"),
    "P": ("حرف جر", "prep"), "CONJ": ("حرف عطف", "conj"), "NEG": ("حرف نفي", "neg"), "ACC": ("حرف نصب", "part"),
    "EMPH": ("حرف توكيد", "part"), "COND": ("أداة شرط", "cond"), "INTG": ("أداة استفهام", "intg"), "SUB": ("حرف مصدري", "part"),
    "RES": ("أداة حصر", "part"), "CERT": ("حرف تحقيق", "part"), "VOC": ("حرف نداء", "voc"), "REM": ("حرف استئناف", "part"),
    "RSLT": ("حرف واقع في جواب الشرط", "part"), "PRO": ("حرف نهي", "part"), "PRP": ("لام التعليل", "part"),
    "CIRC": ("واو الحال", "part"), "SUP": ("حرف زائد", "part"), "PREV": ("حرف كافّ", "part"), "FUT": ("حرف استقبال", "part"),
    "RET": ("حرف إضراب", "part"), "EXP": ("أداة استثناء", "part"), "INC": ("حرف ابتداء", "part"), "CAUS": ("حرف سببية", "part"),
    "IMPV": ("لام الأمر", "part"), "EXL": ("حرف تفصيل", "part"), "AMD": ("حرف استدراك", "part"), "INT": ("حرف تفسير", "part"),
    "ANS": ("حرف جواب", "part"), "EXH": ("حرف تحضيض", "part"), "SUR": ("حرف فجاءة", "part"), "AVR": ("حرف ردع", "part"),
    "INL": ("حروف مقطعة", "inl"), "EQ": ("حرف تسوية", "part"), "COM": ("واو المعية", "part"), "IMPN": ("اسم فعل أمر", "part"),
}
NOUN_KIND = {  # MASAQ stem tags that name the kind of derived noun
    "ADJ_INTENS": ("صيغة مبالغة", "intens"), "ADJ_QUALIT": ("صفة مشبهة", "qualit"), "ADJ_COMP": ("اسم تفضيل", "elative"),
    "GERUND_MEEM": ("مصدر ميمي", "masdar"), "GERUND_INSTANT": ("اسم مرة", "masdar"), "NOUN_TIME_PLACE": ("اسم زمان أو مكان", "timeplace"),
    "NOUN_INSTRUMENT": ("اسم آلة", "instr"), "NOUN_RELATIVE": ("اسم منسوب", "noun"), "NOUN_DIMINUTIVE": ("اسم مصغّر", "noun"),
    "NOUN_NUM": ("اسم عدد", "num"), "NOUN_FIVE": ("من الأسماء الخمسة", "noun"),
}
FORMS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
BAB = {  # form -> (past, present, masdar) for the derived forms
    "II": ("فَعَّلَ", "يُفَعِّلُ", "تَفْعِيل"), "III": ("فَاعَلَ", "يُفَاعِلُ", "مُفَاعَلَة"), "IV": ("أَفْعَلَ", "يُفْعِلُ", "إِفْعَال"),
    "V": ("تَفَعَّلَ", "يَتَفَعَّلُ", "تَفَعُّل"), "VI": ("تَفَاعَلَ", "يَتَفَاعَلُ", "تَفَاعُل"), "VII": ("انْفَعَلَ", "يَنْفَعِلُ", "انْفِعَال"),
    "VIII": ("افْتَعَلَ", "يَفْتَعِلُ", "افْتِعَال"), "IX": ("افْعَلَّ", "يَفْعَلُّ", "افْعِلَال"), "X": ("اسْتَفْعَلَ", "يَسْتَفْعِلُ", "اسْتِفْعَال"),
}
PERF_PASS = {"II": "فُعِّلَ", "III": "فُوعِلَ", "IV": "أُفْعِلَ", "V": "تُفُعِّلَ", "VI": "تُفُوعِلَ", "VII": "انْفُعِلَ", "VIII": "افْتُعِلَ", "X": "اسْتُفْعِلَ"}
IMPF_ACT = {"II": "ُفَعِّلُ", "III": "ُفَاعِلُ", "IV": "ُفْعِلُ", "V": "َتَفَعَّلُ", "VI": "َتَفَاعَلُ", "VII": "َنْفَعِلُ", "VIII": "َفْتَعِلُ", "IX": "َفْعَلُّ", "X": "َسْتَفْعِلُ"}
IMPF_PASS = {"II": "ُفَعَّلُ", "III": "ُفَاعَلُ", "IV": "ُفْعَلُ", "V": "ُتَفَعَّلُ", "VI": "ُتَفَاعَلُ", "VII": "ُنْفَعَلُ", "VIII": "ُفْتَعَلُ", "X": "ُسْتَفْعَلُ"}
IMPV = {"II": "فَعِّلْ", "III": "فَاعِلْ", "IV": "أَفْعِلْ", "V": "تَفَعَّلْ", "VI": "تَفَاعَلْ", "VII": "انْفَعِلْ", "VIII": "افْتَعِلْ", "IX": "افْعَلَّ", "X": "اسْتَفْعِلْ"}
ACT_PCPL = {"I": "فَاعِل", "II": "مُفَعِّل", "III": "مُفَاعِل", "IV": "مُفْعِل", "V": "مُتَفَعِّل", "VI": "مُتَفَاعِل", "VII": "مُنْفَعِل", "VIII": "مُفْتَعِل", "IX": "مُفْعَلّ", "X": "مُسْتَفْعِل"}
PASS_PCPL = {"I": "مَفْعُول", "II": "مُفَعَّل", "III": "مُفَاعَل", "IV": "مُفْعَل", "V": "مُتَفَعَّل", "VI": "مُتَفَاعَل", "VII": "مُنْفَعَل", "VIII": "مُفْتَعَل", "X": "مُسْتَفْعَل"}
ENDING = {"FS": "َة", "FP": "َات", "MP:NOM": "ُونَ", "MP": "ِينَ", "MD:NOM": "َانِ", "MD": "َيْنِ", "FD:NOM": "َتَانِ", "FD": "َتَيْنِ"}
PREFIX = {"1S": "أ", "1P": "ن", "2": "ت", "3FS": "ت", "3FD": "ت"}
PERSON = {"1": "متكلم", "2": "مخاطب", "3": "غائب"}
GENDER = {"M": "مذكر", "F": "مؤنث"}
NUMBER = {"S": "مفرد", "D": "مثنى", "P": "جمع"}

def root_class(root):
    if len(root) == 4: return "رباعي"
    f, e, l = root
    weak = [i for i, c in enumerate(root) if c in "وي"]
    out = []
    if len(weak) == 2: out.append("لفيف مقرون" if weak == [1, 2] else "لفيف مفروق")
    elif weak: out.append({0: "مثال", 1: "أجوف", 2: "ناقص"}[weak[0]])
    elif e == l: out.append("مضعّف")
    hamza = [i for i, c in enumerate(root) if c == "ء"]
    if hamza: out.append("مهموز " + {0: "الفاء", 1: "العين", 2: "اللام"}[hamza[0]])
    return " · ".join(out) or "صحيح سالم"

def map_wazn(stem, root):
    """Replace the root letters of a stem with ف ع ل (ل) — only for roots with no weak or doubled letter."""
    if any(c in "وي" for c in root) or (len(root) == 3 and root[1] == root[2]): return ""
    stem = stem.replace("ٱ", "ا").replace("ٰ", "ا")
    slots, out, r = "فعلل", [], 0
    for ch in stem:
        if ch in HARAKAT:
            out.append(ch); continue
        if r < len(root) and (ch == root[r] or (root[r] == "ء" and ch in HAMZA)):
            out.append(slots[r] if r < 3 or len(root) == 4 else ch); r += 1
        elif ch in "ٓٔ":
            continue
        else:
            out.append(ch)
    if r < len(root): return ""
    w = "".join(out)
    return w[0] + w[1:3].replace("ّ", "", 1) + w[3:] if len(w) > 2 else w  # no shadda on the first letter (it comes from ال)

def strip_case(w): return re.sub("[ًٌٍَُِ]+$", "", w)

def with_vowel(pattern, last):  # give the pattern the stem's final short vowel (or sukun)
    return re.sub("[َُِْ]$", "", pattern) + last if last else pattern

def sarf(word):
    stem = word["stem"]; f = stem["f"]; pos = f.get("POS", "")
    form = next((x for x in FORMS[1:] if f"({x})" in f), "I")
    root = ar(f.get("ROOT", "").replace("A", "'")); masaq_kind = word.get("kind", "")
    label, key = TYPE.get(pos, ("كلمة", "part"))
    pgn = next((x for x in f if re.fullmatch(r"[123][MF]?[SDP]", x)), "")
    gn = next((x for x in f if re.fullmatch(r"[MF][SDP]?", x)), "")
    case = next((x for x in ("NOM", "ACC", "GEN") if x in f), "")
    form_txt = ar(stem["form"]); last = next((c for c in reversed(form_txt) if c in "َُِْ"), "")
    wazn, bab = "", ""
    if pos == "V":
        aspect = "PERF" if "PERF" in f else "IMPV" if "IMPV" in f else "IMPF"
        label = {"PERF": "فعل ماضٍ", "IMPF": "فعل مضارع", "IMPV": "فعل أمر"}[aspect]
        key = {"PERF": "past", "IMPF": "present", "IMPV": "imperative"}[aspect]
        passive = "PASS" in f
        if passive: label += " مبني للمجهول"; key += "_pass"
        if "SP:kaAn" in f or "SP:kaAd" in f: label += " ناسخ"
        if form == "I":
            bab = "ثلاثي مجرد" + (": " + ar(f.get("LEM", "")) if f.get("LEM") else "")
            wazn = map_wazn(form_txt, root)
        else:
            p, pr, m = BAB[form]
            bab = f"{p} – {pr} – {m} ({form})"
            if aspect == "PERF": wazn = with_vowel(PERF_PASS.get(form, p) if passive else p, "ْ" if last == "ْ" else "")
            elif aspect == "IMPV": wazn = with_vowel(IMPV[form], last if last != "ْ" else "")
            else:
                pre = PREFIX.get(pgn) or PREFIX.get(pgn[:1]) or "ي"
                wazn = pre + (IMPF_PASS if passive else IMPF_ACT).get(form, IMPF_ACT[form])
                mood = "َ" if "MOOD:SUBJ" in f else "ْ" if "MOOD:JUS" in f else ""
                if mood: wazn = with_vowel(wazn, mood)
    elif pos in ("N", "ADJ", "PN"):
        if "PCPL" in f:
            active = "ACT" in f
            label, key = ("اسم فاعل", "act_pcpl") if active else ("اسم مفعول", "pass_pcpl")
            wazn = strip_case(map_wazn(form_txt, root)) if form == "I" else ""
            if not wazn:
                base = (ACT_PCPL if active else PASS_PCPL).get(form, "")
                end = ENDING.get(f"{gn}:{case}") or ENDING.get(gn, "") if gn and gn not in ("M", "MS", "F") else ""
                wazn = base + end if base else ""
        elif "VN" in f:
            label, key = "مصدر", "masdar"
            wazn = strip_case(map_wazn(form_txt, root)) or (BAB[form][2] if form != "I" else "")
        elif pos != "PN":
            wazn = strip_case(map_wazn(form_txt, root))
        if masaq_kind in NOUN_KIND and pos != "PN": label, key = NOUN_KIND[masaq_kind]
        if form != "I": bab = "{} – {} – {} ({})".format(*BAB[form], form)
    person = ""
    if pos == "V" and pgn:
        person = " · ".join(filter(None, [PERSON[pgn[0]], NUMBER.get(pgn[-1]), GENDER.get(pgn[1]) if len(pgn) == 3 else ""]))
    elif pos in ("N", "ADJ") and gn:
        person = " · ".join(filter(None, [NUMBER.get(gn[1:]) if len(gn) == 2 else "", GENDER.get(gn[0])]))
    return [S(label), S(key), S(" ".join(root)), S(root_class(root) if len(root) in (3, 4) else ""), S(bab), S(wazn), S(person)]

# ---------------------------------------------------------------- nahw (MASAQ)
ROLE = {  # MASAQ syntactic role -> (Arabic term, case it puts the word in, gloss key)
    "AGNT": ("فاعل", "رفع", "agent"), "SUBJ": ("مبتدأ", "رفع", "mubtada"), "SUBJ_DELA": ("مبتدأ مؤخر", "رفع", "mubtada"),
    "PRED": ("خبر", "رفع", "khabar"), "PASS_SUBJ": ("نائب فاعل", "رفع", "naib"), "SUBJ_COP_V": ("اسم كان أو إحدى أخواتها", "رفع", "kana_ism"),
    "V_COP_PRED": ("خبر كان أو إحدى أخواتها", "نصب", "kana_khabar"), "SUBJ_COP_PART": ("اسم إنّ أو إحدى أخواتها", "نصب", "inna_ism"),
    "PART_COP_PRED": ("خبر إنّ أو إحدى أخواتها", "رفع", "inna_khabar"), "OBJ": ("مفعول به", "نصب", "object"),
    "COGN": ("مفعول مطلق", "نصب", "mutlaq"), "SUBS_COG_ACC": ("نائب عن المفعول المطلق", "نصب", "mutlaq"),
    "PURP": ("مفعول لأجله", "نصب", "purpose"), "COMIT": ("مفعول معه", "نصب", "comit"), "CIRCUM": ("حال", "نصب", "hal"),
    "ACC_SPECIF": ("تمييز", "نصب", "tamyiz"), "ADV_TIME": ("ظرف زمان", "نصب", "advt"), "ADV_PLCE": ("ظرف مكان", "نصب", "advp"),
    "EXCP": ("مستثنى", "نصب", "excp"), "SUBJ_NEG_CAT": ("اسم لا النافية للجنس", "نصب", "inna_ism"), "VOC": ("منادى", "نصب", "voc"),
    "PREP_OBJ": ("اسم مجرور", "جر", "majrur"), "GEN_CONS": ("مضاف إليه", "جر", "mudaf_ilayh"),
    "ADJ": ("نعت", "", "naat"), "CONJ_N": ("اسم معطوف", "", "matuf"), "APPOS": ("بدل", "", "badal"), "INTENCIF": ("توكيد", "", "tawkid"),
    "EXPLET": ("ضمير فصل", "", "part"), "NOUN_CONS": ("مضاف", "", "noun"), "NUM_COMP": ("جزء من العدد المركب", "", "num"),
    "PREP": ("حرف جر", "-", "prep"), "CONJ": ("حرف عطف", "-", "conj"), "ANNUL_PART": ("حرف ناسخ (إنّ أو إحدى أخواتها)", "-", "part"),
    "PART_JUSSIVE": ("حرف جزم", "-", "part"), "SUBJUNC_PART": ("حرف نصب", "-", "part"), "PART_CONDITION": ("أداة شرط", "-", "cond"),
    "VOC_PART": ("حرف نداء", "-", "voc"), "PART_INTERROG": ("حرف استفهام", "-", "intg"), "CERT_PART": ("حرف تحقيق", "-", "part"),
    "PART_EXCEPT": ("أداة استثناء", "-", "part"), "NEG": ("حرف نفي", "-", "neg"), "NEG_MAA": ("ما النافية", "-", "neg"),
    "NEG_CAT": ("لا النافية للجنس", "-", "neg"), "NEG_PROH": ("لا الناهية", "-", "neg"), "SUBOR_CONJ": ("حرف مصدري ونصب", "-", "part"),
    "SUBOR_ANN_CONJ": ("حرف مصدري ناسخ", "-", "part"), "COMPL": ("حرف مصدري", "-", "part"), "PART_PREV": ("حرف كافّ", "-", "part"),
    "PART_INHIB": ("حرف", "-", "part"), "ACRON": ("حروف مقطعة", "-", "inl"),
    "INTERJ_CV": ("اسم فعل أمر", "-", "part"), "INTERJ_PV": ("اسم فعل ماضٍ", "-", "part"), "INTERJ_IV": ("اسم فعل مضارع", "-", "part"),
}
VERB_ROLE = {"IV": "فعل مضارع", "IV_PASS": "فعل مضارع مبني للمجهول", "IV_COP": "فعل مضارع ناسخ", "CV": "فعل أمر", "CV_COP": "فعل أمر ناسخ"}
VERB_TAG = {"PV": "فعل ماضٍ", "PV_PASS": "فعل ماضٍ مبني للمجهول", "IV": "فعل مضارع", "IV_PASS": "فعل مضارع مبني للمجهول",
            "CV": "فعل أمر", "UNINFLECTED_VERB": "فعل جامد"}
INVAR_KIND = {"JONT_PRON": "ضمير متصل", "DISJ_INV_PRON": "ضمير منفصل", "DISJ_PRON": "ضمير منفصل", "REL_PRON": "اسم موصول",
              "DEM_NOUN": "اسم إشارة", "COND_NOUN": "اسم شرط", "INTROG_NOUN": "اسم استفهام"}
PARTICLE_TAG = {"NEG_PART": "حرف نفي", "INTERROG": "حرف استفهام", "INTERROG_PART": "حرف استفهام", "CONJ": "حرف عطف", "PREP": "حرف جر",
                "FUTURE_PART": "حرف استقبال", "FUT_PART": "حرف استقبال", "FUTUR_PART": "حرف استقبال", "CERT_PART": "حرف تحقيق",
                "EMPHATIC_NUN": "نون التوكيد", "KAAFA_MAKFOUFA": "كافّة ومكفوفة", "YES_NO_RESP_PART": "حرف جواب", "VOC_PART": "حرف نداء"}
CASE = {"NOMINATIVE": ("مرفوع", "رفعه", "رفع"), "ACCUSATIVE": ("منصوب", "نصبه", "نصب"), "GENITIVE": ("مجرور", "جره", "جر"), "JUSSIVE": ("مجزوم", "جزمه", "جزم")}
MARKER = {"DHAMMA": "الضمة", "FATHA": "الفتحة", "KASRA": "الكسرة", "SUKUN": "السكون", "NUN": "ثبوت النون", "DEL_NUN": "حذف النون",
          "YAA": "الياء", "WAW": "الواو", "ALIF": "الألف", "IMP_DHAMMA": "الضمة المقدرة", "IMP_FATHA": "الفتحة المقدرة",
          "IMP_KASRA": "الكسرة المقدرة", "FATHA_DIPTOTE": "الفتحة نيابة عن الكسرة لأنه ممنوع من الصرف", "DEL_VOWEL": "حذف حرف العلة"}
BUILT = {"SUKUN": "السكون", "FATHA": "الفتح", "DHAMMA": "الضم", "KASRA": "الكسر", "DEL_VOWEL": "حذف حرف العلة", "DEL_NUN": "حذف النون"}
PHRASE = {"PHRASE": "شبه الجملة", "VERB_SNT": "الجملة الفعلية", "NOM_SNT": "الجملة الاسمية", "COND_SNT": "جملة الشرط"}

def irab(r, whole_word, rows):
    """One classic iʿrāb line for a MASAQ segment, or None when the segment carries no iʿrāb."""
    tag, role, inv = r["Morph_Tag"], r["Syntactic_Role"], r["Invariable_Declinable"]
    case, mark = r["Case_Mood"], r["Case_Mood_Marker"]
    stem = r["Morph_Type"] == "Stem"
    if not role and not (stem and tag in VERB_TAG): return None
    built = inv not in ("DECLN", "") or case == "INVARIABLE"
    pron_suffix = r["Morph_Type"] != "Stem" and ("PRON" in tag or "SUFF_SUBJ" in tag or "SUFF_DO" in tag or tag == "None")
    if pron_suffix and case not in CASE: built = True
    if pron_suffix and r["Segmented_Word"] in ("ون", "وا", "و"): mark = "SUKUN"  # واو الجماعة
    if role in VERB_ROLE or (not role and tag in VERB_TAG):
        head, key = VERB_ROLE.get(role) or VERB_TAG.get(tag, "فعل"), "verb"
        if case in CASE:  # MASAQ sometimes keeps a verb's case marker on its prefix row
            built = False
            better = {"NOMINATIVE": ("NUN", "DHAMMA", "IMP_DHAMMA"), "ACCUSATIVE": ("DEL_NUN", "FATHA", "IMP_FATHA"), "JUSSIVE": ("DEL_NUN", "SUKUN", "DEL_VOWEL")}[case] if case != "GENITIVE" else ()
            if mark not in better:
                mark = next((x["Case_Mood_Marker"] for x in rows if x["Case_Mood"] == case and x["Case_Mood_Marker"] in better), better[1] if better else mark)
        if built: text = head + (" مبني على " + BUILT[mark] if mark in BUILT else " مبني")
        elif case in CASE: text = f"{head} {CASE[case][0]} وعلامة {CASE[case][1]} {MARKER.get(mark, '')}".strip()
        else: text = head
    else:
        term, role_case, key = ROLE.get(role, ("", "", "part"))
        if not term: return None
        if role_case == "-":  # particles: no grammatical position
            text = term + (" مبني على " + BUILT[mark] if mark in BUILT else "") + " لا محل له من الإعراب"
        elif built:
            kind = INVAR_KIND.get(inv) or PARTICLE_TAG.get(tag) or ("ضمير متصل" if r["Morph_Type"] != "Stem" and ("PRON" in tag or "SUFF_SUBJ" in tag or "SUFF_DO" in tag) else "")
            place = CASE[case][2] if case in CASE else role_case
            text = " ".join(filter(None, [kind, "مبني على " + BUILT[mark] if mark in BUILT else "مبني", "في محل " + place if place else "", term]))
        elif case in CASE:
            adj = "" if CASE[case][0] in term else " " + CASE[case][0]
            text = f"{term}{adj} وعلامة {CASE[case][1]} {MARKER.get(mark, '')}".strip()
        else:
            text = term
        if r["Possessive_Construct"] == "CONSTRUCT": text += "، وهو مضاف"
    if r["Phrase"] in PHRASE and r["Phrasal_Function"] in ROLE:
        t, c, _ = ROLE[r["Phrasal_Function"]]
        text += f"؛ و{PHRASE[r['Phrase']]} في محل {c} {t}" if c not in ("", "-") else f"؛ و{PHRASE[r['Phrase']]} {t}"
    seg = r["Segmented_Word"]
    particle = ROLE.get(role, ("", ""))[1] == "-"
    label = whole_word if stem and not particle else ("" if seg in ("", "None", "(null)") else seg)
    return label, text, key

# ---------------------------------------------------------------- alignment
def skeleton(w):
    w = MARKS.sub("", w).replace("ٱ", "ا")
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ة", "ه"), ("ؤ", "ء"), ("ئ", "ء")): w = w.replace(a, b)
    return re.sub("[اويء ]", "", w)

def align(ours, theirs):
    """Map each of our words to MASAQ word indices, allowing 2→1 and 1→2 joins."""
    n, m = len(ours), len(theirs)
    if n == m: return [[i] for i in range(n)]
    sim = lambda a, b: SequenceMatcher(None, a, b).ratio()
    so, st = [skeleton(w) for w in ours], [skeleton(w) for w in theirs]
    INF = float("inf"); best = [[INF] * (m + 1) for _ in range(n + 1)]; back = {}
    best[0][0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            if best[i][j] == INF: continue
            for di, dj in ((1, 1), (2, 1), (1, 2)):
                if i + di > n or j + dj > m: continue
                cost = 1 - sim("".join(so[i:i + di]), "".join(st[j:j + dj])) + (0.3 if (di, dj) != (1, 1) else 0)
                if best[i][j] + cost < best[i + di][j + dj]:
                    best[i + di][j + dj] = best[i][j] + cost; back[(i + di, j + dj)] = (i, j)
    out, cur = [None] * n, (n, m)
    while cur != (0, 0):
        pi, pj = back[cur]
        for k in range(pi, cur[0]): out[k] = list(range(pj, cur[1]))
        cur = (pi, pj)
    return out

# ---------------------------------------------------------------- build
def main():
    corpus = {}
    for line in open(os.path.join(G, "quranic-corpus-morphology-0.4.txt"), encoding="utf8"):
        if line.startswith(("#", "LOCATION")) or not line.strip(): continue
        loc, form, tag, feats = line.rstrip("\n").split("\t")
        s, v, w, _ = map(int, loc.strip("()").split(":"))
        parts = feats.split("|")
        f = {}
        for p in parts:
            k, _, val = p.partition(":")
            if k in ("POS", "LEM", "ROOT", "MOOD", "SP"): f[k] = val
            if k in ("MOOD", "SP"): f[p] = True
            f[p] = True
        word = corpus.setdefault((s, v, w), {"segs": []})
        word["segs"].append((form, tag, f))
        if "STEM" in f and "stem" not in word: word["stem"] = {"form": form, "f": f}
    masaq = {}
    for r in csv.DictReader(open(os.path.join(G, "MASAQ.csv"), encoding="utf8")):
        masaq.setdefault((int(r["Sura_No"]), int(r["Verse_No"])), {}).setdefault(int(r["Word_No"]), []).append(r)
    quran = json.load(open(os.path.join(SRC, "quran.json"), encoding="utf8"))["surahs"]
    word_key, ranked = lemmas.load()
    entry = {key: (arabic if not key.startswith("FORM:") else "", rank) for rank, (key, arabic, _, _) in enumerate(ranked, 1)}
    meaning = {}
    for line in open(os.path.join(SRC, "lemma_meanings.txt"), encoding="utf8"):
        if line.startswith("#") or not line.strip(): continue
        rank, ru, kk = line.strip().split("|")
        meaning[int(rank)] = (ru.strip(), kk.strip())
    out, stats = {}, {"words": 0, "with_irab": 0, "with_wazn": 0, "with_meaning": 0, "realigned_verses": 0}
    for sid, verses in quran.items():
        out[sid] = []
        for v in verses:
            mw = masaq.get((int(sid), v["n"]), {})
            mkeys = sorted(mw)
            mapping = align(v["w"], [mw[k][0]["Word"] for k in mkeys])
            if len(mkeys) != len(v["w"]): stats["realigned_verses"] += 1
            row = []
            for i, w in enumerate(v["w"]):
                cw = corpus[(int(sid), v["n"], i + 1)]
                rows = [r for j in mapping[i] for r in mw[mkeys[j]]]
                kind = next((r["Morph_Tag"] for r in rows if r["Morph_Type"] == "Stem" and r["Morph_Tag"] in NOUN_KIND), "")
                cw["kind"] = kind
                fields = sarf(cw)
                role_key, lines = "", []
                for r in rows:
                    got = irab(r, w, rows)
                    if got:
                        label, text, key = got
                        lines += [S(label), S(text)]
                        if r["Morph_Type"] == "Stem" and not role_key: role_key = key
                lemma_ar, rank = entry[word_key[(int(sid), v["n"], i + 1)]]
                ru, kk = meaning.get(rank, ("", ""))
                stats["words"] += 1; stats["with_irab"] += bool(lines); stats["with_wazn"] += bool(strings[fields[5]]); stats["with_meaning"] += bool(ru)
                row.append(fields + [S(role_key), S(lemma_ar), S(ru), S(kk)] + lines)
            out[sid].append(row)
    json.dump({"s": strings, "q": out}, open(os.path.join(SRC, "grammar.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print(stats, "strings:", len(strings), "bytes:", os.path.getsize(os.path.join(SRC, "grammar.json")))

if __name__ == "__main__":
    main()
