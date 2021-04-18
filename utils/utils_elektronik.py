import re
from utils.ms_lines import find_lines
from easydict import EasyDict

class TabelleGerate():
    def __init__(self):
        self.Position, self.BU, self.Geräteart, self.SB, self.VSU, self.Klauseln, self.Hersteller_Modul, self.Hersteller_Wechselrichter, self.Leistung, self.Baujahr, self.Stand, self.Anzahl, self.Haftzeit = \
                    [[] for _ in range(13)]
        self.last_index = 0 # last index of table
        self.kw = {}

    def versicherte_vache_elements(self, m):
        for blk_id, df_blk in self.df_block_group:
            df_blk = find_lines(df_blk)
            # -------------------------- Hersteller_Modul
            if len(df_blk[df_blk['text'].str.contains("(?i)Modul")]) and len(df_blk[df_blk['text'].str.contains('(?i)Hersteller')]):
                tmp_Modul_line = list(df_blk.query('text.str.contains("(?i)modul")')['line'])
                if len(tmp_Modul_line):
                    tmp_Modul_line = tmp_Modul_line[0]
                    tmp_Hersteller_Modul = ' '.join(df_blk[df_blk["line"] == tmp_Modul_line]['text'])
                    try:
                        tmp = re.split('Module', tmp_Hersteller_Modul)[1]
                        pattern = re.compile(r'^\W')
                        tmp = re.sub(pattern, '', tmp)
                        if len(tmp) > 2:
                            self.Hersteller_Modul[m] = tmp
                        else:
                            tmp_Modul_line += 1
                            self.Hersteller_Modul[m] = ' '.join(df_blk[df_blk['line'] == tmp_Modul_line]['text'])
                    except:
                        pass
            elif list(df_blk[df_blk['text'].str.contains("Photovo") & df_blk['text'].str.contains("module")]['text']):
                line_modul = list(df_blk.query('text.str.contains("(?i)modul")')['line'])
                if line_modul:
                    line_modul = line_modul[0]
                    tmp_Hersteller_Modul = ' '.join(df_blk.query('line == @line_modul')['text'])
                    tmp = re.split('module', tmp_Hersteller_Modul)[1]
                    tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                    if len(tmp) > 2:
                        self.Hersteller_Modul[m] = tmp
                    else:
                        line_modul += 1
                        self.Hersteller_Modul[m] = ' '.join(df_blk.query('line == @line_modul')['text'])
            # -------------------------- Hersteller_Wechselrichter
            if len(df_blk[df_blk['text'].str.contains("Wechselrichter")]['text']) > 0 and\
                    len(df_blk[df_blk['text'].str.contains("Verkabelung")]['text']) > 0:
                line_Wechselrichter = list(df_blk.query('text.str.contains("Verkabelung")')['line'])
                if line_Wechselrichter:
                    line_Wechselrichter = line_Wechselrichter[0]
                    tmp_Wechselrichter = ' '.join(df_blk.query('line == @line_Wechselrichter')['text'])
                    tmp = re.split("Verkabelung", tmp_Wechselrichter)[1]
                    tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                    if len(tmp) > 2:
                        self.Hersteller_Wechselrichter[m] = tmp
                    else:
                        line_Wechselrichter += 1
                        self.Hersteller_Wechselrichter[m] = ' '.join(df_blk.query('line == @line_Wechselrichter')['text'])
            elif len(df_blk[df_blk['text'].str.contains("Wechselrichter")]) and len(
                    df_blk[df_blk['text'].str.contains('Hersteller')]):
                tmp_Wechselrichter_line = list(df_blk.query('text.str.contains("Wechselrichter")')['line'])
                if len(tmp_Wechselrichter_line) == 1:
                    tmp_Wechselrichter_line = tmp_Wechselrichter_line[0]
                    tmp_Wechselrichter = ' '.join(df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                    tmp = re.split('Wechselrichter', tmp_Wechselrichter)[1]
                    tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                    if len(tmp) > 2:
                        self.Hersteller_Wechselrichter[m] = tmp
                    else:
                        tmp_Wechselrichter_line += 1
                        self.Hersteller_Wechselrichter[m] = ' '.join(
                            df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
            # -------------------------- Baujahr
            tmp_Baujahr_line = list(df_blk.query('text.str.contains("Baujahr")')['line'])
            if len(tmp_Baujahr_line) == 1:
                tmp_Baujahr_line = tmp_Baujahr_line[0]
                tmp_Baujahr = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])
                tmp = re.split('Baujahr', tmp_Baujahr)[1]
                tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                if len(tmp) > 2:
                    self.Baujahr[m] = tmp
                else:
                    tmp_Baujahr_line += 1
                    self.Baujahr[m] = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])

            # -------------------------- Anzahl
            tmp_Anzahl_line = list(df_blk.query('text.str.contains("Anzahl")')['line'])
            if len(tmp_Anzahl_line):
                tmp_Anzahl_line = tmp_Anzahl_line[0]
                tmp_Anzahl = ' '.join(df_blk[df_blk['line'] == tmp_Anzahl_line]['text'])
                tmp = re.split('Anzahl', tmp_Anzahl)[1]
                tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                if len(tmp) > 2:
                    self.Anzahl[m] = tmp
                else:
                    tmp_Anzahl_line += 1
                    self.Anzahl[m] = ' '.join(df_blk[df_blk['line'] == tmp_Anzahl_line]['text'])

            #  ------------------------- Leistung section
            tmp_Leistung_line = list(df_blk.query('text.str.contains("Nennleistung")')['line'])
            if len(tmp_Leistung_line) == 1:
                tmp_Leistung_line = tmp_Leistung_line[0]
                tmp_Leistung = ' '.join(df_blk.query('line == @tmp_Leistung_line')['text'])
                tmp = re.split('Nennleistung', tmp_Leistung)[1]
                pattern = re.compile(r'^\W')
                tmp = re.sub(pattern, '', tmp)
                if len(tmp) > 2:
                    self.Leistung[m] = tmp
                else:
                    tmp_Leistung_line += 1
                    self.Leistung[m] = ' '.join(df_blk.query('line = @tmp_Leistung_line')['text'])
            # -------- Haftzeit
            line_Haftzeit = list(df_blk.query('text.str.contains("Haftzeit")')['line'])
            if line_Haftzeit:
                line_Haftzeit = line_Haftzeit[0]
                Haftzeit = ' '.join(df_blk.query('line == @line_Haftzeit')['text'])
                tmp = re.split('Haftzeit', Haftzeit)[1]
                tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                if len(tmp) > 2:
                    self.Haftzeit[m] = tmp
                else:
                    line_Haftzeit += 1
                    self.Haftzeit[m] = ' '.join(df_blk.query('line == @line_Haftzeit')['text'])

    def tabelle_gerate(self, df, first_page=None):
        position_word = df[df['text'].str.contains('Posi-')]
        if len(position_word) != 1:
            return None
        left_posi, top_posi = list(position_word['left'])[0], list(position_word['top'])[0]
        top_horizontal_line = list(df[(df['top'] > top_posi) & (df['text'] == "<LINE>")]['top'])[
            -2]  # find top_coordinate of horizontal line from table
        df_table = df[(df['top'] > top_posi) & (df['top'] < top_horizontal_line)]  # whole table
        df_number_position = df_table[
            (df_table['left'] > left_posi - 40) & (df_table['left'] < left_posi + 40)]  # number column
        number_pos = list(df_number_position[df_number_position['text'].str.contains('^\d{,2}$')]['text'])

        if not first_page:
            # Position, Geräteart, SB, VSU, Klauseln, Hersteller_Modul, Hersteller_Wechselrichter, Leistung, Baujahr, Stand, Anzahl = \
            #     self.Position, self.Geräteart, self.SB, self.VSU, self.Klauseln, self.Hersteller_Modul, self.Hersteller_Wechselrichter, \
            #     self.Leistung, self.Baujahr, self.Stand, self.Anzahl
            # last_index = self.last_index
            # kw = self.kw

            # ------- continues from previous page
            top_horizontal_line_1 = list(df[(df['top'] > top_posi) & (df['text'] == "<LINE>")]['top'])[1]
            if number_pos:
                top_number = list(df_number_position[df_number_position['text'] == number_pos[0]]['top'])[0]
                df_number = df_table[(df_table['top'] < top_number - 20) & (df_table['top'] > top_horizontal_line_1 - 20)]
            else:
                df_number = df_table[(df_table['top'] > top_horizontal_line_1 - 20) & (df_table['top'] < top_horizontal_line - 20)]
            self.df_block_group = tuple(df_number.groupby('block'))
            try:
                self.versicherte_vache_elements(self.Position[-1])
            except:
                pass
            # ------- BU
            line_betrieb = list(df_number[df_number['text'].str.contains('Betr&ebsunter')]['line'])
            if len(line_betrieb) == 1:
                df_betrieb = df_number[df_number['line'] == line_betrieb[0]]['text']
                try:
                    self.BU[self.Position[-1]] = list(df_betrieb[df_betrieb.str.contains('\d\.\d')])[0]
                except:
                    pass

            if not number_pos:

                self.kw = {'Position':self.Position, 'Geräteart': self.Geräteart, 'SB': self.SB, 'VSU': self.VSU, 'Klauseln': self.Klauseln,'Hersteller Modul': self.Hersteller_Modul,
                      'Hersteller Wechselrichter': self.Hersteller_Wechselrichter, 'Leistung': self.Leistung, 'Baujahr': self.Baujahr, 'Stand': self.Stand, 'Anzahl': self.Anzahl, 'BU': self.BU, 'Haftzeit': self.Haftzeit}

                return self.kw

        self.Stand.extend(['None'])
        self.Geräteart.extend(['None'] * len(number_pos)), self.SB.extend(
            ['None'] * len(number_pos)), \
        self.VSU.extend(['None'] * len(number_pos)), self.Klauseln.extend(['None'] * len(number_pos)), \
        self.Hersteller_Modul.extend(['None'] * len(number_pos)), self.Hersteller_Wechselrichter.extend(
            ['None'] * len(number_pos)), self.Leistung.extend(['None'] * len(number_pos)), self.Baujahr.extend(
            ['None'] * len(number_pos)), self.Anzahl.extend(
            ['None'] * len(number_pos)), self.BU.extend(['None']*len(number_pos)), self.Haftzeit.extend(['None']*len(number_pos))
        if len(number_pos) == 0:
            return None
        # ----------- Stand
        line_stand = list(df_table[df_table['text'].str.contains('(?i)stand')]['line'])
        if len(line_stand):
            line_stand = line_stand[0]
        stand_line = df_table[df_table['line'] == line_stand]
        tmp = stand_line[stand_line['text'].str.contains('\d{4}')]['text'].to_list()
        if len(tmp) == 1:
            self.Stand[-1] = tmp[0]
        left_stand = list(df_table.query('text.str.contains("(?i)stand")')['left'])
        for m in range(len(number_pos) - 1):
            self.Position.append(int(number_pos[m]) - 1)
            top_number = list(df_number_position[df_number_position['text'] == number_pos[m]]['top'])[0]
            top_next_number = list(df_number_position[df_number_position['text'] == number_pos[m + 1]]['top'])[0]
            df_number = df_table[
                (df_table['top'] > top_number - 20) & (df_table['top'] < top_next_number - 20)]  # Whole row
            # ------ Geräteart, VSU and SB column
            df_line_pos = df_number[(df_number['top'] < top_number + 50) & (df_number['top'] > top_number - 10)]
            text_line_pos = df_line_pos.query("text.str.contains('\d{2}') | text.str.contains('[a-zA-Z]')")
            self.Geräteart[self.Position[-1]] = text_line_pos.iloc[0]['text']
            if left_stand:
                try:
                    text_line_pos = text_line_pos[(text_line_pos['left'] > left_stand[0] - 60)]
                    self.VSU[self.Position[-1]] = text_line_pos.iloc[0]['text']
                    self.SB[self.Position[-1]] = text_line_pos.iloc[1]['text']
                except:
                    pass

            self.df_block_group = tuple(df_number.groupby('block'))
            try:
                self.versicherte_vache_elements(self.Position[-1])
            except:
                pass
            # ------- BU
            line_betrieb = list(df_number[df_number['text'].str.contains('Betriebsunter|Betrlebsunter')]['line'])
            if len(line_betrieb) == 1:
                df_betrieb = df_number[df_number['line'] == line_betrieb[0]]['text']
                try:
                    self.BU[self.Position[-1]] = list(df_betrieb[df_betrieb.str.contains('\d\.\d')])[0]
                except:
                    pass

        # ---------- last position of table
        self.Position.append(int(number_pos[-1]) - 1)
        top_number = list(df_number_position[df_number_position['text'] == number_pos[-1]]['top'])[0]
        df_number = df_table[df_table['top'] > top_number - 20]  # Whole row
        # ------ Geräteart, VSU and SB column
        df_line_pos = df_number[(df_number['top'] < top_number + 50) & (df_number['top'] > top_number - 10)]
        text_line_pos = df_line_pos.query("text.str.contains('\d{2}') | text.str.contains('[a-zA-Z]')")
        try:
            self.Geräteart[self.Position[-1]] = text_line_pos.iloc[0]['text']
        except:
            pass
        if left_stand:
            left_stand = left_stand[0]
            text_line_pos = text_line_pos[(text_line_pos['left'] > left_stand - 60)]
            try:
                self.VSU[self.Position[-1]] = text_line_pos.iloc[0]['text']
                self.SB[self.Position[-1]] = text_line_pos.iloc[1]['text']
            except:
                pass
        self.df_block_group = tuple(df_number.groupby('block'))
        self.versicherte_vache_elements(self.Position[-1])

        # ------- BU
        line_betrieb = list(df_number[df_number['text'].str.contains('Betriebsunter|Betrlebsunter')]['line'])
        if len(line_betrieb) == 1:
            df_betrieb = df_number[df_number['line'] == line_betrieb[0]]['text']
            try:
                self.BU[self.Position[-1]] = list(df_betrieb[df_betrieb.str.contains('\d\.\d')])[0]
            except:
                pass
        self.kw = {'Position': self.Position, 'Geräteart': self.Geräteart, 'SB': self.SB, 'VSU': self.VSU,
                   'Klauseln': self.Klauseln, 'Hersteller Modul': self.Hersteller_Modul,
                   'Hersteller Wechselrichter': self.Hersteller_Wechselrichter, 'Leistung': self.Leistung,
                   'Baujahr': self.Baujahr, 'Stand': self.Stand, 'Anzahl': self.Anzahl, 'BU': self.BU, 'Haftzeit': self.Haftzeit}

        return self.kw