#
# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from collections import OrderedDict
from lingua_nostra.lang.parse_common import invert_dict
from lingua_nostra.lang.parse_common import QuestionType, QuestionSubType
import simplematch as sm

_FUNCTION_NOT_IMPLEMENTED_WARNING = "The requested function is not implemented in English."

_ARTICLES_EN = {'a', 'an', 'the'}

_NUM_STRING_EN = {
    0: 'zero',
    1: 'one',
    2: 'two',
    3: 'three',
    4: 'four',
    5: 'five',
    6: 'six',
    7: 'seven',
    8: 'eight',
    9: 'nine',
    10: 'ten',
    11: 'eleven',
    12: 'twelve',
    13: 'thirteen',
    14: 'fourteen',
    15: 'fifteen',
    16: 'sixteen',
    17: 'seventeen',
    18: 'eighteen',
    19: 'nineteen',
    20: 'twenty',
    30: 'thirty',
    40: 'forty',
    50: 'fifty',
    60: 'sixty',
    70: 'seventy',
    80: 'eighty',
    90: 'ninety'
}

_FRACTION_STRING_EN = {
    2: 'half',
    3: 'third',
    4: 'forth',
    5: 'fifth',
    6: 'sixth',
    7: 'seventh',
    8: 'eigth',
    9: 'ninth',
    10: 'tenth',
    11: 'eleventh',
    12: 'twelveth',
    13: 'thirteenth',
    14: 'fourteenth',
    15: 'fifteenth',
    16: 'sixteenth',
    17: 'seventeenth',
    18: 'eighteenth',
    19: 'nineteenth',
    20: 'twentyith'
}

_LONG_SCALE_EN = OrderedDict([
    (100, 'hundred'),
    (1000, 'thousand'),
    (1000000, 'million'),
    (1e12, "billion"),
    (1e18, 'trillion'),
    (1e24, "quadrillion"),
    (1e30, "quintillion"),
    (1e36, "sextillion"),
    (1e42, "septillion"),
    (1e48, "octillion"),
    (1e54, "nonillion"),
    (1e60, "decillion"),
    (1e66, "undecillion"),
    (1e72, "duodecillion"),
    (1e78, "tredecillion"),
    (1e84, "quattuordecillion"),
    (1e90, "quinquadecillion"),
    (1e96, "sedecillion"),
    (1e102, "septendecillion"),
    (1e108, "octodecillion"),
    (1e114, "novendecillion"),
    (1e120, "vigintillion"),
    (1e306, "unquinquagintillion"),
    (1e312, "duoquinquagintillion"),
    (1e336, "sesquinquagintillion"),
    (1e366, "unsexagintillion")
])

_SHORT_SCALE_EN = OrderedDict([
    (100, 'hundred'),
    (1000, 'thousand'),
    (1000000, 'million'),
    (1e9, "billion"),
    (1e12, 'trillion'),
    (1e15, "quadrillion"),
    (1e18, "quintillion"),
    (1e21, "sextillion"),
    (1e24, "septillion"),
    (1e27, "octillion"),
    (1e30, "nonillion"),
    (1e33, "decillion"),
    (1e36, "undecillion"),
    (1e39, "duodecillion"),
    (1e42, "tredecillion"),
    (1e45, "quattuordecillion"),
    (1e48, "quinquadecillion"),
    (1e51, "sedecillion"),
    (1e54, "septendecillion"),
    (1e57, "octodecillion"),
    (1e60, "novendecillion"),
    (1e63, "vigintillion"),
    (1e66, "unvigintillion"),
    (1e69, "uuovigintillion"),
    (1e72, "tresvigintillion"),
    (1e75, "quattuorvigintillion"),
    (1e78, "quinquavigintillion"),
    (1e81, "qesvigintillion"),
    (1e84, "septemvigintillion"),
    (1e87, "octovigintillion"),
    (1e90, "novemvigintillion"),
    (1e93, "trigintillion"),
    (1e96, "untrigintillion"),
    (1e99, "duotrigintillion"),
    (1e102, "trestrigintillion"),
    (1e105, "quattuortrigintillion"),
    (1e108, "quinquatrigintillion"),
    (1e111, "sestrigintillion"),
    (1e114, "septentrigintillion"),
    (1e117, "octotrigintillion"),
    (1e120, "noventrigintillion"),
    (1e123, "quadragintillion"),
    (1e153, "quinquagintillion"),
    (1e183, "sexagintillion"),
    (1e213, "septuagintillion"),
    (1e243, "octogintillion"),
    (1e273, "nonagintillion"),
    (1e303, "centillion"),
    (1e306, "uncentillion"),
    (1e309, "duocentillion"),
    (1e312, "trescentillion"),
    (1e333, "decicentillion"),
    (1e336, "undecicentillion"),
    (1e363, "viginticentillion"),
    (1e366, "unviginticentillion"),
    (1e393, "trigintacentillion"),
    (1e423, "quadragintacentillion"),
    (1e453, "quinquagintacentillion"),
    (1e483, "sexagintacentillion"),
    (1e513, "septuagintacentillion"),
    (1e543, "ctogintacentillion"),
    (1e573, "nonagintacentillion"),
    (1e603, "ducentillion"),
    (1e903, "trecentillion"),
    (1e1203, "quadringentillion"),
    (1e1503, "quingentillion"),
    (1e1803, "sescentillion"),
    (1e2103, "septingentillion"),
    (1e2403, "octingentillion"),
    (1e2703, "nongentillion"),
    (1e3003, "millinillion")
])

_ORDINAL_BASE_EN = {
    1: 'first',
    2: 'second',
    3: 'third',
    4: 'fourth',
    5: 'fifth',
    6: 'sixth',
    7: 'seventh',
    8: 'eighth',
    9: 'ninth',
    10: 'tenth',
    11: 'eleventh',
    12: 'twelfth',
    13: 'thirteenth',
    14: 'fourteenth',
    15: 'fifteenth',
    16: 'sixteenth',
    17: 'seventeenth',
    18: 'eighteenth',
    19: 'nineteenth',
    20: 'twentieth',
    30: 'thirtieth',
    40: "fortieth",
    50: "fiftieth",
    60: "sixtieth",
    70: "seventieth",
    80: "eightieth",
    90: "ninetieth",
    1e2: "hundredth",
    1e3: "thousandth"
}

_SHORT_ORDINAL_EN = {
    1e6: "millionth",
    1e9: "billionth",
    1e12: "trillionth",
    1e15: "quadrillionth",
    1e18: "quintillionth",
    1e21: "sextillionth",
    1e24: "septillionth",
    1e27: "octillionth",
    1e30: "nonillionth",
    1e33: "decillionth"
    # TODO > 1e-33
}
_SHORT_ORDINAL_EN.update(_ORDINAL_BASE_EN)

_LONG_ORDINAL_EN = {
    1e6: "millionth",
    1e12: "billionth",
    1e18: "trillionth",
    1e24: "quadrillionth",
    1e30: "quintillionth",
    1e36: "sextillionth",
    1e42: "septillionth",
    1e48: "octillionth",
    1e54: "nonillionth",
    1e60: "decillionth"
    # TODO > 1e60
}
_LONG_ORDINAL_EN.update(_ORDINAL_BASE_EN)

# negate next number (-2 = 0 - 2)
_NEGATIVES_EN = {"negative", "minus"}

# sum the next number (twenty two = 20 + 2)
_SUMS_EN = {'twenty', '20', 'thirty', '30', 'forty', '40', 'fifty', '50',
            'sixty', '60', 'seventy', '70', 'eighty', '80', 'ninety', '90'}


def _generate_plurals_en(originals):
    """
    Return a new set or dict containing the plural form of the original values,

    In English this means all with 's' appended to them.

    Args:
        originals set(str) or dict(str, any): values to pluralize

    Returns:
        set(str) or dict(str, any)

    """
    # TODO migrate to https://github.com/MycroftAI/lingua-franca/pull/36
    if isinstance(originals, dict):
        return {key + 's': value for key, value in originals.items()}
    return {value + "s" for value in originals}


_MULTIPLIES_LONG_SCALE_EN = set(_LONG_SCALE_EN.values()) | \
                            _generate_plurals_en(_LONG_SCALE_EN.values())

_MULTIPLIES_SHORT_SCALE_EN = set(_SHORT_SCALE_EN.values()) | \
                             _generate_plurals_en(_SHORT_SCALE_EN.values())

# split sentence parse separately and sum ( 2 and a half = 2 + 0.5 )
_FRACTION_MARKER_EN = {"and"}

# decimal marker ( 1 point 5 = 1 + 0.5)
_DECIMAL_MARKER_EN = {"point", "dot"}

_STRING_NUM_EN = invert_dict(_NUM_STRING_EN)
_STRING_NUM_EN.update(_generate_plurals_en(_STRING_NUM_EN))

_SPOKEN_EXTRA_NUM_EN = {
    "half": 0.5,
    "halves": 0.5,
    "couple": 2
}
_STRING_SHORT_ORDINAL_EN = invert_dict(_SHORT_ORDINAL_EN)
_STRING_LONG_ORDINAL_EN = invert_dict(_LONG_ORDINAL_EN)

sm.register_type("abbr", r"([A-Z]\.*){2,}s?")


def _generate_entity_rules(entities, qwords=None):
    qwords = qwords or ["what", "which"]
    rules = []
    # add plurals
    entities += [e + "s" for e in entities
                 if not e.endswith("s") and not e.endswith("*")]

    for ent in entities:
        rules += [
            "name * " + ent + " {query}"
        ]
        for qw in qwords:
            rules += [
                qw + " " + ent + " {query}",
                qw + " {query} " + ent,
                qw + " {property} " + ent + " {query}",
                "{query} " + qw + " " + ent
            ]
    return rules


_QUESTION_RULES_EN = {

    QuestionSubType.ABBREVIATION: [
        "what * acronym {query}",
        "What * abbreviat* {query}",
        "what does {query} stand for *",
        "what does {query} stand for"
    ],
    QuestionSubType.ABBREVIATION_EXPLANATION: [
        "what * {query:abbr} stand for *",
        "what * {query:abbr} stand for",
        "what * {query:abbr} mean",
        "* what * {query:abbr} mean",
        "* what * {query:abbr} mean *",
        "* what * {query:abbr} stand for *",
        "* what * {query:abbr} stand for",
        "What * {query:abbr}",
        "What * {query:abbr} abbreviat* *",
        "{query:abbr} * acronym *",
        "{query:abbr} * stand for",
        "{query:abbr} * stand for *",
        "{query:abbr} * abbreviat* *",
    ],

    QuestionSubType.NUMERIC_DATE: [
        "what date {query}",
        "what season {query}",
        "what {query} season",
        "what century {query}",
        "which century {query}",
        "what {query} birthday",
        "what {query} birthdate",
        "which date {query}",
        "which dates {query}",
        "what dates {query}",
        "what year {query}",
        "which year {query}",
        "what day {query}",
        "{query} in what day*",
        "{query} in what year*",
        "{query} in what month*",
        "{query} in what week*",
        "{query} in what decade*",
        "{query} in what century",
        "{query} on what day*",
        "{query} on what year*",
        "{query} on what month*",
        "{query} on what week*",
        "{query} on what decade*",
        "{query} on what century",
        "{query} in which day*",
        "{query} in which year*",
        "{query} in which month*",
        "{query} in which week*",
        "{query} in which decade*",
        "{query} in whichcentury",
        "{query} on which day*",
        "{query} on which year*",
        "{query} on which month*",
        "{query} on which week*",
        "{query} on which decade*",
        "{query} on which century",
        "{query} on which date",
        "{query} in which date",
        "{query} on what date",
        "{query} in what date",
        "which day {query}",
        "what month {query}",
        "which month {query}",
        "what months {query}",
        "which months {query}",
        "which season {query}",
        "what * date {query}",
        "what * year {query}",
        "what * day {query}",
        "what * month {query}",
        "what * week {query}",
        "what * decade {query}",
        "what * dates {query}",
        "what * years {query}",
        "what * days {query}",
        "what * months {query}",
        "what * weeks {query}",
        "what * decades {query}",
        "what * centuries {query}",
        "when did {query}",
        "when was {query}",
        "when were {query}",
        "when is {query}",
        "when are {query}",
        "What geological time {query}",
        "when is {query} day",
        "when is {query} day of *",
        "when do {query}",
        "when does {query}",
        "when will {query}",
    ],
    QuestionSubType.NUMERIC_ORDINAL: ["what chapter {query}",
                                      "where {query} rank *"],
    QuestionSubType.NUMERIC_COUNT: [
        "How many {query}",
        "How much {query}",
        "How many {query} in *",
        "How much {query} in *",
        "how often are {query}",
        "how often is {query}",
        "What * number {query}",
        "What * average {query}",
        "What * population {query}",
        "How * population {query}",
        "How * {query} population",
        "What is {query} population",
        "What * death toll {query}",
    ],
    QuestionSubType.NUMERIC_VOLSIZE: [
        "how big is {query}",
        "how large is {query}",
        "What is the acreage of {query}",
        "What is the size {query}",
        "What is the volume {query}"
    ],
    QuestionSubType.NUMERIC_OTHER: [
        "What is the * point {query}",
        "How often {query}",
        "how loud {query}",
        "what amount {query}",
        "what * score {query}",
        "what * number* {query}",
        "what * shoe size* {query}",
        "what * statistic* {query}",
        "What * all-time * high {query}",
        "What * all time * high {query}",
        "What * all-time * low {query}",
        "What * all time * low {query}",
        "What * average {query}",
        "What * chemical reactivity {query}",

        "What * frequency {query}",
        "What * horsepower {query}",
        "What * latitude {query}",
        "What * longitude {query}",
        "What * heart rate {query}",
        "What * quantity {query}",
        "How large {query} population ?",
        "What number {query}",
        "What {query} IQ",
        "What * {query:int}",
        "What * {query:int} *",
        "* {num1:int}+{num2:int} *",
        "* {num1:int}-{num2:int} *",
        "* {num1:int}/{num2:int} *",
        "* {num1:int}*{num2:int} *",
        "{num1:int}+{num2:int}",
        "{num1:int}-{num2:int}",
        "{num1:int}/{num2:int}",
        "{num1:int}*{num2:int}",
    ],
    QuestionSubType.NUMERIC_DISTANCE: [
        "How far away {query}",
        "How deep {query}",
        "How high {query}",
        "How long is {query}",
        "How long was {query}",
        "How long were {query}",
        "How far is {query} from *",
        "How far {query}",
        "How far * from {query} to *",
        "How far {query} from *",
        "How long is {query} in miles",
        "How long is {query} in *meters",
        "How tall {query}",
        "How wide {query}",
        "What * depth {query}",
        "What * diameter {query}",
        "What * radius {query}",
        "What * distance* {query}",
        "What * elevation {query}",
        "What * length* {query}",
        "What * width* {query}",
        "What {query} depth",
        "What {query} diameter",
        "What {query} radius",
        "What {query} distance",
        "What {query} elevation",
        "What {query} length",
        "What {query} width",
        "What are the dimensions {query}",
        "What is the wingspan {query}",
        "What * record * longest {query}"
    ],
    QuestionSubType.NUMERIC_WEIGHT: [
        "What * weigh* {query}",
        "How much {query} weigh*",
        "What {query} weigh*",
        "How many pounds {query}",
        "* how much {query} weigh*",
        "* how much {query} weigh* *"
    ],
    QuestionSubType.NUMERIC_TEMPERATURE: [
        "How cold {query}",
        "How hot {query}",
        "{query} what is the temperature*",
        "What is {query} temperature*",
        "What * temperature* {query}",
        "What * Fahrenheit {query}",
        "What {query} degree* Fahrenheit",
        "What {query} degree* centigrade",
        "What {query} degree* celcius",
        "What is the temperature at {query}",
        "What is the temperature of {query}"
    ],
    QuestionSubType.NUMERIC_SPEED: [
        "How fast {query}",
        "What * speed of {query}",
        "What is the speed {query}"
    ],
    QuestionSubType.NUMERIC_PERIOD: [
        "For how long is {query}",
        "How long did {query}",
        "How long do* {query}",
        "How long after {query}",
        "How long ago {query}",
        "How long has {query}",
        "How long should {query}",
        "How long was {query}",
        "How long time {query}",
        "How long would it take {query}",
        "How long is {query} gestation",
        "How old {query}",
        "what age is {query}",
        "what * age {query}",
        "what * life expectancy {query}",
        "what * time it takes {query}",
        "what * average time {query}",
        "what age {query} live*",
        "what is {query} age",
        "{query} how old",
        "{query} for how long",
        "{query} for how long *",
        "What * life span {query}",
        "What * gestation period {query}",
        "At what age {query}"
    ],
    QuestionSubType.NUMERIC_PERCENTAGE: [
        "what percentage {query}",
        "what * percentage {query}",
        "what* percentage {query}",
        "what fraction of {query}",
        "what * fraction of {query}",
        "what* fraction of {query}",
        "What is the {query} rate in *",
        "What are the chances of {query}",
        "What is the chance of {query}",
        "what percent* {query}",
        "what ratio of {query}",
        "what * approval rating {query}",
        "What * probability {query}",
        "What * probabilities {query}",
        "What * odds {query}",
        "What * rate {query}",
        "What is {query} tax rate",
        "What {query} tax *",
    ],
    QuestionSubType.NUMERIC_MONEY: [
        "how much {query}",
        "{query} cost how much",
        "{query} worth what in * dollar*",
        "{query} worth what in * euro*",
        "{query} worth what in * pounds",
        "* conversion rate {query} euro*",
        "* conversion rate {query} pound*",
        "* conversion rate {query} dollar*",
        "What amount of money {query}",
        "What * amount of money {query}",
        "What {query} worth",
        "What {query} cost",
        "What {query} price",
        "What {query} wage",
        "What {query} tax",
        "What {query} price *",
        "What {query} wage *",
        "What {query} tax *",
        "What {query} cost of *",
        "What {query} cost for *",
        "What * ticket fare {query}",
        "What * salary {query}",
        "What * income {query}",
        "What * fine for {query}",
        "What * price for {query}",
        "What * price of {query}",
        "What * exchange rate {query}",
        "What {query} minimum wage",
        "What {query} cost *",
        "What {query} get paid",
        "What {query} get paid *",
        "What can you be fined {query}",
        "What debt {query}",
        "What debts {query}"
    ],

    QuestionSubType.ENTITY_CURRENCY: [
        "What is the money {query}",
        "What currency {query}",
        "what money {query}",
        "which money {query}",
        "What * money they use *",
        "What currency {query}",
        "What money * used {query}",
        "What type of currency {query}"

    ],
    QuestionSubType.ENTITY_ANIMAL: [
        "What * animal {query}",
        "What animal* {query}",
        "Which animal* {query}",
        "What * animals {query}",
        "What {query} animal*"
    ],
    QuestionSubType.ENTITY_PLANT: [
        "What * plant {query}",
        "What * plants {query}",
        "What * flower {query}",
        "What * flowers {query}",
        "What {query} plant*",
        "What {query} flower*",
    ],
    QuestionSubType.ENTITY_COLOR: [
        "What * colors {query}",
        "What * colours {query}",
        "What * color {query}",
        "What * colour {query}",
        "What {query} color*",
        "What {query} colour*"
    ],
    QuestionSubType.ENTITY_INSTRUMENT: [
        "What * instrument* {query}",
        "What instrument* {query}",
        "What {query} instrument*"
    ],

    QuestionSubType.HUMAN_INDIVIDUAL:
        ["Who was {query}",
         "Who is {query}",
         "who* {query}",
         "what {query} *name",
         "what person {query}",
         "name {query}",
         "what {query} secret identity",
         "what * identity of {query}",
         "{query} whom",
         "what {query} died *",
         "{query} whom by *",
         "with whom {query}",
         "which member {query}",
         "what *man {query}",
         ] + _generate_entity_rules(
            ["character", "*name", "person", "*president", "senator", "artist",
             "leader", "ruler", "actor", "actress", "queen", "king",
             "celebrit*", "author", "daughter", "son", "girl", "boy"]),

    QuestionSubType.LOCATION_CITY: [
        "what city {query}",
        "what is {country} capital",
        "what capital {query}",
        "what {query} city",
        "what {query} cities",
        "what {query} city *",
        "what {query} cities *",
        "what county is {query}",
        "what * capital of {query}",
        "what * city {query}",
        "which city {query}",
        "which * city {query}",
        "{query} what city",
        "{query} which city",
        "{query} what {nationality} city",
        "what {nationality} capital {query}",
        "what {nationality} city {query}",
        "{query} which {nationality} city",
        "{query} what cities",
        "{query} which cities",
        "{query} what {nationality} cities",
        "{query} which {nationality} cities",
        "what town {query}",
        "what {query} town",
        "what * town {query}",
        "which town {query}",
        "which * town {query}",
        "{query} what town",
        "{query} which town",
        "{query} what {nationality} town",
        "{query} which {nationality} town"
    ],
    QuestionSubType.LOCATION_COUNTRY: [
        "which countr* {query}",
        "what countr* {query}",
        "which nation* {query}",
        "what nation* {query}",

        "what {query} countr*",
        "what {query} nation*",

        "what {property} countr* {query}",
        "what {property} nation* {query}",
        "which {property} countr* {query}",
        "which {property} nation* {query}",

        "{query} what countr*",
        "{query} which countr*",
        "{query} what nation*",
        "{query} which nation*",

        "name * countr* {query}",
        "name * nation* {query}"
    ],
    QuestionSubType.LOCATION_STATE: [
        "which state* {query}",
        "what state* {query}",
        "which province* {query}",
        "what province* {query}",

        "what {query} state*",
        "what {query} province*",

        "what {property} state* {query}",
        "what {property} province* {query}",
        "which {property} state* {query}",
        "which {property} province* {query}",

        "{query} what state*",
        "{query} which state*",
        "{query} what province*",
        "{query} which province*",

        "name * state* {query}",
        "name * province* {query}"
    ],
    QuestionSubType.LOCATION_OTHER:
        [
            "where {query}",
            "{query} live in",
            "name {query} in {place}",
            "name {query} located {place}",
            "{query} from {place} to where",
            "what {place} were {query} in",
            "what {query} visit in {place}",
            "location of {place}",
            "What {query} birthplace",
            "What * birthplace {query}",
            "which way {query}"

        ] + _generate_entity_rules(
            ["area", "place", "river", "mountain*", "colony", "part of",
             "landmark", "battlefield", "avenue", "street", "continent",
             "*land", "city structure", "building", "bridge", "desert",
             "sea", "address", "*site", "territor*", "ocean", "body of water",
             "National Park", "hemisphere", "lake", "planet"
             ]),
    QuestionSubType.LOCATION_MOUNTAIN:
        [
            "Where * highest point {query}"
        ] + _generate_entity_rules(
            ["mountain*", "peak"],
            ["what", "which", "where"]),
}
