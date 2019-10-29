# -*- coding: utf-8  -*-
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
import unittest
from datetime import datetime, time

from lingua_franca.parse import get_gender
from lingua_franca.parse import extract_datetime
from lingua_franca.parse import extract_number
from lingua_franca.parse import normalize


class TestNormalize(unittest.TestCase):
    """
        Test cases for Spanish parsing
    """

    def test_articles_es(self):
        self.assertEqual(normalize("esta es el test",
                                   lang="es", remove_articles=True),
                         "esta es test")
        self.assertEqual(
            normalize("esta es la frase", lang="es", remove_articles=True),
            "esta es frase")
        self.assertEqual(
            normalize("y otra prueba", lang="es", remove_articles=True),
            "otra prueba")
        self.assertEqual(normalize("esta es la prueba extra",
                                   lang="es",
                                   remove_articles=False), 
                                   "esta es la prueba extra")

    def test_extractnumber_es(self):
        self.assertEqual(extract_number("esta es la primera prueba", lang="es"),
                         1)
        self.assertEqual(extract_number("este es el test 2", lang="es"), 2)
        self.assertEqual(extract_number("este es el segundo test", lang="es"),
                         2)
        self.assertEqual(extract_number("este es un tercio de test",
                                        lang="es"), 1.0 / 3.0)
        self.assertEqual(extract_number(u"este es el test número cuatro",
                                        lang="es"), 4)
        self.assertEqual(extract_number("un tercio de taza", lang="es"),
                         1.0 / 3.0)
        self.assertEqual(extract_number("3 tazas", lang="es"), 3)
        self.assertEqual(extract_number("1/3 tazas", lang="es"), 1.0 / 3.0)
        self.assertEqual(extract_number("quarto de hora", lang="es"), 0.25)
        self.assertEqual(extract_number("1/4 hora", lang="es"), 0.25)
        self.assertEqual(extract_number("u cuarto de hora", lang="es"), 0.25)
        self.assertEqual(extract_number("2/3 gota", lang="es"), 2.0 / 3.0)
        self.assertEqual(extract_number("3/4 de gota", lang="es"), 3.0 / 4.0)
        self.assertEqual(extract_number(u"1 y 3/4 de cafe", lang="es"), 1.75)
        self.assertEqual(extract_number("1 cafe y medio", lang="es"), 1.5)
        self.assertEqual(extract_number("un cafe y un medio", lang="es"), 1.5)
        self.assertEqual(extract_number("un cafe y medio", lang="es"), 1.5)
        self.assertEqual(
            extract_number("tres cuartos de chocolate", lang="es"),
            3.0 / 4.0)
        self.assertEqual(extract_number("tres cuarto de chocolate",
                                        lang="es"), 3.0 / 4.0)
        self.assertEqual(extract_number("siete coma cinco", lang="es"), 7.5)
        self.assertEqual(extract_number("siete coma 5", lang="es"), 7.5)
        self.assertEqual(extract_number("siete punto cinco", lang="es"), 7.5)
        self.assertEqual(extract_number("siete punto 5", lang="es"), 7.5)
        self.assertEqual(extract_number("siete y medio", lang="es"), 7.5)
        # TODO: Following must be "siete CON ochenta, and so on"
        self.assertEqual(extract_number("siete y ochenta", lang="es"), 7.80)
        self.assertEqual(extract_number("siete y ocho", lang="es"), 7.8)
        self.assertEqual(extract_number("siete y cero ocho",
                                        lang="es"), 7.08)
        self.assertEqual(extract_number("siete y cero cero ocho",
                                        lang="es"), 7.008)
        self.assertEqual(extract_number("veinte treceavos", lang="es"),
                         20.0 / 13.0)
        # TODO: next is WRONG, it should be 6.660 or "seis coma sesenta y seis"
        self.assertEqual(extract_number("seis coma seiscentos sesenta",
                                        lang="es"), 6.66)
        self.assertEqual(extract_number("seiscientos sesenta y seis",
                                        lang="es"), 666)
        # TODO: next should be pronounced "coma", not "punto"
        self.assertEqual(extract_number("seiscentos punto cero seis",
                                        lang="es"), 600.06)
        self.assertEqual(extract_number("seiscentos punto cero cero seis",
                                        lang="es"), 600.006)
        self.assertEqual(extract_number("seiscentos punto cero cero cero seis",
                                        lang="es"), 600.0006)

    def test_agressive_pruning_es(self):
        self.assertEqual(normalize("una palabra", lang="es"),
                         "1 palabra")
        self.assertEqual(normalize("esta palabra un", lang="es"),
                         "palabra 1")
        self.assertEqual(normalize("el hombre lo golpeó", lang="es"),
                         "hombre golpeó")
        self.assertEqual(normalize("quién dijo mentiras aquél día", lang="es"),
                         "quién dijo mentiras día")

    def test_spaces_es(self):
        self.assertEqual(normalize("  este   es  el    test", lang="es"),
                         "este test")
        self.assertEqual(normalize("  estas   son las    pruebas  ", lang="es"),
                         "estas son pruebas")
        self.assertEqual(normalize("  esto   es  un    test", lang="es",
                                   remove_articles=False),
                         "esto 1 test")

    def test_numbers_es(self):
        self.assertEqual(normalize("este es el un dos tres test", lang="es"),
                         "este 1 2 3 test")
        self.assertEqual(normalize("es la siete ocho nueve  prueba", lang="es"),
                         "es 7 8 9 prueba")
        self.assertEqual(
            normalize("test cero diez once doce trece", lang="es"),
            "test 0 10 11 12 13")
        # TODO: next result shouldn't be "1666" ?
        self.assertEqual(
            normalize("test mil seiscentos sesenta y seis", lang="es",
                      remove_articles=False),
            "test 1000 600 60 6")
        self.assertEqual(
            normalize("test siete y medio", lang="es",
                      remove_articles=False),
            "test 7 medio")
        self.assertEqual(
            normalize("test dos punto nueve", lang="es"),
            "test 2 punto 9")
        self.assertEqual(
            normalize("test ciento y nueve", lang="es",
                      remove_articles=False),
            "test 100 9")
        # TODO: veinte y uno (20,1) != veintiuno (21)
        self.assertEqual(
            normalize("test veinte y 1", lang="es"),
            "test 20 1")

    def test_extractdatetime_es(self):
        def extractWithFormat(text):
            date = datetime(2017, 6, 27, 0, 0)
            [extractedDate, leftover] = extract_datetime(text, date,
                                                         lang="es")
            extractedDate = extractedDate.strftime("%Y-%m-%d %H:%M:%S")
            return [extractedDate, leftover]

        def testExtract(text, expected_date, expected_leftover):
            res = extractWithFormat(text)
            self.assertEqual(res[0], expected_date)
            self.assertEqual(res[1], expected_leftover)

        testExtract(u"qué día es hoy",
                    "2017-06-27 00:00:00", u"día")
        testExtract(u"qué día es mañana",
                    "2017-06-28 00:00:00", u"día")
        testExtract(u"qué día fue ayer",
                    "2017-06-26 00:00:00", u"día")
        testExtract(u"qué día fue antes de ayer",
                    "2017-06-25 00:00:00", u"día")
        # TODO: in spanish next the expression "antes de ayer"
        # is more common than "ante ayer", but both are correct
        testExtract(u"qué día fue ante ayer",
                    "2017-06-25 00:00:00", u"día")
        testExtract(u"qué día fue ante ante ayer",
                    "2017-06-24 00:00:00", u"día")
        testExtract("prepara la cena en 5 días",
                    "2017-07-02 00:00:00", "prepara cena")
        testExtract("cómo está el tiempo para pasado mañana?",
                    "2017-06-29 00:00:00", "cómo tiempo")
        # TODO: next should be just "recuérdame"
        testExtract(u"recuérdame a las 10:45 pm",
                    "2017-06-27 22:45:00", u"recuérdame a")
        testExtract("cómo está el tiempo el viernes por la mañana?",
                    "2017-06-30 08:00:00", "cómo tiempo")
        testExtract("recuérdame que llame a mi madre de aquí "
                    u"a 8 semanas y 2 días",
                    "2017-08-24 00:00:00", u"recuérdame llame madre")
        testExtract("Toca black metal 2 días después del viernes",
                    "2017-07-02 00:00:00", "toca black metal")
        testExtract("Toca satanic black metal 2 días después del viernes",
                    "2017-07-02 00:00:00", "toca satanic black metal")
        testExtract("Toca super black metal 2 días a partir de este viernes",
                    "2017-07-02 00:00:00", "toca super black metal")
        testExtract("Comienza la invasión a las 3:45 pm del jueves",
                    "2017-06-29 15:45:00", "comienza invasión")
        testExtract("el lunes, comprar queso",
                    "2017-07-03 00:00:00", "comprar queso")
        testExtract(u"Toca el cumpleaños feliz de aquí a 5 años",
                    "2022-06-27 00:00:00", "toca cumpleaños feliz")
        testExtract(u"envía Skype a mamá el próximo jueves a las 12:45 pm",
                    "2017-06-29 12:45:00", "envía Skype mamá")
        testExtract(u"¿Cómo está el tiempo este viernes?",
                    "2017-06-30 00:00:00", "cómo tiempo")
        testExtract(u"¿Cómo está el tiempo este viernes por la tarde?",
                    "2017-06-30 15:00:00", "cómo tiempo")
        testExtract(u"¿Cómo está el tiempo este viernes por la mañana?",
                    "2017-06-30 04:00:00", "cómo tiempo")
        testExtract(u"¿Cómo está el tiempo este viernes a medianoche?",
                    "2017-06-30 00:00:00", "cómo tiempo")
        testExtract(u"¿Cómo está el tiempo este viernes a mediodía?",
                    "2017-06-30 12:00:00", "cómo tiempo")
        # TODO: "evening" does not exist in spanish, but many says "tarde noche"
        testExtract(u"¿Cómo está el tiempo este viernes por la tarde noche?",
                    "2017-06-30 19:00:00", "cómo tiempo")
        testExtract(u"¿Cómo está el tiempo este viernes por la mañana?",
                    "2017-06-30 10:00:00", "cómo tiempo")
        testExtract("recuérdame que llame a mamá el 3 de agosto",
                    "2017-08-03 00:00:00", "recuérdamen llame mamá")
        testExtract(u"comprar cuchillos el 13 de mayo",
                    "2018-05-13 00:00:00", "comprar cuchillos")
        testExtract(u"gasta dinero el día 13 de mayo",
                    "2018-05-13 00:00:00", "gasta dinero")
        testExtract(u"compra velas el 13 de mayo",
                    "2018-05-13 00:00:00", "compra velas")
        testExtract(u"bebe cerveza el 13 de mayo",
                    "2018-05-13 00:00:00", "bebe cerveza")
        testExtract("cómo está el tiempo 1 día después de mañana",
                    "2017-06-29 00:00:00", "cómo tiempo")
        testExtract(u"cómo está el tiempo a las 0700 horas",
                    "2017-06-27 07:00:00", "cómo tiempo")
        testExtract(u"cómo está el tiempo mañana a las 7 en punto",
                    "2017-06-28 07:00:00", "cómo tiempo")
        testExtract(u"cómo está el tiempo mañana a las 2 de la tarde",
                    "2017-06-28 14:00:00", "cómo tiempo")
        testExtract(u"cómo está el tiempo mañana a las 2",
                    "2017-06-28 02:00:00", "cómo tiempo")
        testExtract(u"cómo está el tiempo a las 2 de la tarde del próximo viernes.",
                    "2017-06-30 14:00:00", "cómo tiempo")
        testExtract("recuerda que me despierte en 4 anos",
                    "2021-06-27 00:00:00", "recuerda despierte")
        testExtract("recuerda que me despierte en 4 anos y 4 días",
                    "2021-07-01 00:00:00", "recuerda despierte")
        testExtract("duerme 3 días después de mañana",
                    "2017-07-02 00:00:00", "dorme")
        testExtract("marca consulta para 2 semanas y 6 días después del sábado",
                    "2017-07-21 00:00:00", "marca consulta")
        testExtract(u"la fiesta empieza a las 8 en punto del viernes noche",
                    "2017-06-29 20:00:00", "fiesta empieza")

    def test_extractdatetime_default_es(self):
        default = time(9, 0, 0)
        anchor = datetime(2017, 6, 27, 0, 0)
        res = extract_datetime(
            'cita para 2 semanas y 6 días después del sábado',
            anchor, lang='es-es', default_time=default)
        self.assertEqual(default, res[0].time())


class TestExtractGender(unittest.TestCase):
    def test_gender_es(self):
        # words with well defined grammatical gender rules
        self.assertEqual(get_gender("vaca", lang="es"), "f")
        self.assertEqual(get_gender("cabalo", lang="es"), "m")
        self.assertEqual(get_gender("vacas", lang="es"), "f")

        # words specifically defined in a lookup dictionary
        self.assertEqual(get_gender("hombre", lang="es"), "m")
        self.assertEqual(get_gender("mujer", lang="es"), "f")
        self.assertEqual(get_gender("hombres", lang="es"), "m")
        self.assertEqual(get_gender("mujeres", lang="es"), "f")

        # words where gender rules do not work but context does
        self.assertEqual(get_gender("buey", lang="es"), None)
        self.assertEqual(get_gender("buey", "el buey come hierba", lang="es"), "m")
        self.assertEqual(get_gender("hombre", "este hombre come bueyes",
                                    lang="es"), "m")
        self.assertEqual(get_gender("cantante", lang="es"), None)
        self.assertEqual(get_gender("cantante", "esa cantante es muy buena",
                                    lang="es"), "f")


if __name__ == "__main__":
    unittest.main()
