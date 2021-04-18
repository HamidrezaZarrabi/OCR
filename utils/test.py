import re
from utils.ms_lines import find_lines
from easydict import EasyDict

class TabelleGerate():
    def __init__(self):
        self.Position, self.Geräteart, self.SB, self.VSU, self.Klauseln, self.Hersteller_Modul, self.Hersteller_Wechselrichter, self.Leistung, self.Baujahr, self.Stand, self.Anzahl = \
                    [[] for _ in range(11)]
        self.last_index = 0 # last index of table
        self.kw = {}
    def tabelle_gerate(self, df, first_page=None):
        if first_page:
            Position, Geräteart, SB, VSU, Klauseln, Hersteller_Modul, Hersteller_Wechselrichter, Leistung, Baujahr, Stand, Anzahl =\
                self.Position, self.Geräteart, self.SB, self.VSU, self.Klauseln, self.Hersteller_Modul, self.Hersteller_Wechselrichter,\
                self.Leistung, self.Baujahr, self.Stand, self.Anzahl
            last_index = self.last_index
            kw = self.kw
            position_word = df[df['text'].str.contains('Posi-')]
            assert (len(position_word) == 1)
            left_posi, top_posi = list(position_word['left'])[0], list(position_word['top'])[0]
            top_horizontal_line = list(df[(df['top'] > top_posi) & (df['text'] == "<LINE>")]['top'])[
                2]  # find top_coordinate of horizontal line from table
            df_table = df[(df['top'] > top_posi) & (df['top'] < top_horizontal_line)]  # whole table
            df_number_position = df_table[
                (df_table['left'] > left_posi - 40) & (df_table['left'] < left_posi + 40)]  # number column
            number_pos = list(df_number_position[df_number_position['text'].str.contains('^\d{,2}$')]['text'])
            Position.extend(['None'] * len(number_pos)), Geräteart.extend(['None'] * len(number_pos)), SB.extend(
                ['None'] * len(number_pos)), \
            VSU.extend(['None'] * len(number_pos)), Klauseln.extend(['None'] * len(number_pos)), \
            Hersteller_Modul.extend(['None'] * len(number_pos)), Hersteller_Wechselrichter.extend(
                ['None'] * len(number_pos)), Leistung.extend(['None']*len(number_pos)), Baujahr.extend(['None']*len(number_pos)), Stand.extend(['None']*len(number_pos)), Anzahl.extend(['None']*len(number_pos))
            # ----------- Stand
            line_stand = list(df_table[df_table['text'].str.contains('(?i)stand')]['line'])[0]
            stand_line = df_table[df_table['line'] == line_stand]
            stand = list(stand_line[stand_line['text'].str.contains('\d')]['text'])[0]
            left_stand = list(df_table.query('text.str.contains("(?i)stand")')['left'])
            for m in range(len(number_pos) - 1):
                Position[m] = number_pos[m]
                top_number = list(df_number_position[df_number_position['text'] == number_pos[m]]['top'])[0]
                top_next_number = list(df_number_position[df_number_position['text'] == number_pos[m + 1]]['top'])[0]
                df_number = df_table[
                    (df_table['top'] > top_number - 20) & (df_table['top'] < top_next_number - 20)]  # Whole row
                # ------ Geräteart, VSU and SB column
                df_line_pos = df_number[(df_number['top'] < top_number + 50) & (df_number['top'] > top_number - 10)]
                text_line_pos = df_line_pos.query("text.str.contains('\d{2}') | text.str.contains('[a-zA-Z]')")
                Geräteart[m] = text_line_pos.iloc[0]['text']
                if len(left_stand) == 1:
                    text_line_pos = text_line_pos[(text_line_pos['left'] > left_stand[0] - 60)]
                    VSU[m] = text_line_pos.iloc[0]['text']
                    SB[m] = text_line_pos.iloc[1]['text']

                df_block_group = tuple(df_number.groupby('block'))
                for blk_id, df_blk in df_block_group:
                    df_blk = find_lines(df_blk)
                    # -------------------------- Hersteller_Modul
                    if len(df_blk[df_blk['text'].str.contains("Modul")]) and len(df_blk[df_blk['text'].str.contains('Hersteller')]):
                        tmp_Modul_line = list(df_blk.query('text.str.contains("Modul")')['line'])
                        if len(tmp_Modul_line) == 1:
                            tmp_Modul_line = tmp_Modul_line[0]
                            tmp_Hersteller_Modul = ' '.join(df_blk[df_blk["line"] == tmp_Modul_line]['text'])
                            tmp = re.split('Module', tmp_Hersteller_Modul)[1]
                            pattern = re.compile(r'^\W')
                            tmp = re.sub(pattern, '', tmp)
                            if len(tmp) > 2:
                                Hersteller_Modul[m] = tmp
                            else:
                                tmp_Modul_line += 1
                                Hersteller_Modul[m] = ' '.join(df_blk[df_blk['line'] == tmp_Modul_line]['text'])

                    # -------------------------- Hersteller_Wechselrichter
                    if len(df_blk[df_blk['text'].str.contains("Wechselrichter")]) and len(
                            df_blk[df_blk['text'].str.contains('Hersteller')]):
                        tmp_Wechselrichter_line = list(df_blk.query('text.str.contains("Wechselrichter")')['line'])
                        if len(tmp_Wechselrichter_line) == 1:
                            tmp_Wechselrichter_line = tmp_Wechselrichter_line[0]
                            tmp_Wechselrichter = ' '.join(df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                            tmp = re.split('Wechselrichter', tmp_Wechselrichter)[1]
                            tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                            if len(tmp) > 2:
                                Hersteller_Wechselrichter[m] = tmp
                            else:
                                tmp_Wechselrichter_line += 1
                                Hersteller_Wechselrichter[m] = ' '.join(df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                    # -------------------------- Baujahr
                    tmp_Baujahr_line = list(set(df_blk.query('text.str.contains("Baujahr")')['line']))
                    if len(tmp_Baujahr_line) == 1:
                        tmp_Baujahr_line = tmp_Baujahr_line[0]
                        tmp_Baujahr = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])
                        tmp = re.split('Baujahr', tmp_Baujahr)[1]
                        tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                        if len(tmp) > 2:
                            Baujahr[m] = tmp
                        else:
                            tmp_Baujahr_line += 1
                            Baujahr[m] = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])

                    #  ------------------------- Leistung section
                    tmp_Leistung_line = list(set(df_blk.query('text.str.contains("Nennleistung")')['line']))
                    if len(tmp_Leistung_line) == 1:
                        tmp_Leistung_line = tmp_Leistung_line[0]
                        tmp_Leistung = ' '.join(df_blk.query('line == @tmp_Leistung_line')['text'])
                        tmp = re.split('Nennleistung', tmp_Leistung)[1]
                        pattern = re.compile(r'^\W')
                        tmp = re.sub(pattern, '', tmp)
                        if len(tmp) > 2:
                            Leistung[m] = tmp
                        else:
                            tmp_Leistung_line += 1
                            Leistung[m] = ' '.join(df_blk.query('line = @tmp_Leistung_line')['text'])

            # ---------- last position of table
            Position[-1] = number_pos[-1]
            top_number = list(df_number_position[df_number_position['text'] == number_pos[-1]]['top'])[0]
            df_number = df_table[df_table['top'] > top_number - 20]  # Whole row
            # ------ Geräteart, VSU and SB column
            df_line_pos = df_number[(df_number['top'] < top_number + 50) & (df_number['top'] > top_number - 10)]
            text_line_pos = df_line_pos.query("text.str.contains('\d{2}') | text.str.contains('[a-zA-Z]')")
            Geräteart[-1] = text_line_pos.iloc[0]['text']
            if len(left_stand) == 1:
                left_stand = left_stand[0]
                text_line_pos = text_line_pos[(text_line_pos['left'] > left_stand - 60)]
                VSU[-1] = text_line_pos.iloc[0]['text']
                SB[-1] = text_line_pos.iloc[1]['text']

            df_block_group = tuple(df_number.groupby('block'))
            for blk_id, df_blk in df_block_group:
                df_blk = find_lines(df_blk)
                # -------------------------- Hersteller_Modul
                if len(df_blk[df_blk['text'].str.contains("Modul")]) and len(df_blk[df_blk['text'].str.contains('Hersteller')]):
                    tmp_Modul_line = list(df_blk.query('text.str.contains("Modul")')['line'])
                    if len(tmp_Modul_line) == 1:
                        tmp_Modul_line = tmp_Modul_line[0]
                        tmp_Hersteller_Modul = ' '.join(df_blk[df_blk["line"] == tmp_Modul_line]['text'])
                        tmp = re.split('Module', tmp_Hersteller_Modul)[1]
                        pattern = re.compile(r'^\W')
                        tmp = re.sub(pattern, '', tmp)
                        if len(tmp) > 2:
                            Hersteller_Modul[-1] = tmp
                        else:
                            tmp_Modul_line += 1
                            Hersteller_Modul[-1] = ' '.join(df_blk[df_blk['line'] == tmp_Modul_line]['text'])

                # -------------------------- Hersteller_Wechselrichter
                if len(df_blk[df_blk['text'].str.contains("Wechselrichter")]) and len(
                        df_blk[df_blk['text'].str.contains('Hersteller')]):
                    tmp_Wechselrichter_line = list(df_blk.query('text.str.contains("Wechselrichter")')['line'])
                    if len(tmp_Wechselrichter_line) == 1:
                        tmp_Wechselrichter_line = tmp_Wechselrichter_line[0]
                        tmp_Wechselrichter = ' '.join(
                            df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                        tmp = re.split('Wechselrichter', tmp_Wechselrichter)[1]
                        tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                        if len(tmp) > 2:
                            Hersteller_Wechselrichter[-1] = tmp
                        else:
                            tmp_Wechselrichter_line += 1
                            Hersteller_Wechselrichter[-1] = ' '.join(
                                df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                # -------------------------- Baujahr
                tmp_Baujahr_line = list(set(df_blk.query('text.str.contains("Baujahr")')['line']))
                if len(tmp_Baujahr_line) == 1:
                    tmp_Baujahr_line = tmp_Baujahr_line[0]
                    tmp_Baujahr = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])
                    tmp = re.split('Baujahr', tmp_Baujahr)[1]
                    tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                    if len(tmp) > 2:
                        Baujahr[-1] = tmp
                    else:
                        tmp_Baujahr_line += 1
                        Baujahr[-1] = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])

                #  ------------------------- Leistung section
                tmp_Leistung_line = list(df_blk.query('text.str.contains("Nennleistung")')['line'])
                if len(tmp_Leistung_line) == 1:
                    tmp_Leistung_line = tmp_Leistung_line[0]
                    tmp_Leistung = ' '.join(df_blk.query('line == @tmp_Leistung_line')['text'])
                    tmp = re.split('Nennleistung', tmp_Leistung)[1]
                    pattern = re.compile(r'^\W')
                    tmp = re.sub(pattern, '', tmp)
                    if len(tmp) > 2:
                        Leistung[-1] = tmp
                    else:
                        tmp_Leistung_line += 1
                        Leistung[-1] = ' '.join(df_blk.query('line = @tmp_Leistung_line')['text'])
            last_index += (len(number_pos) - 1)
            self.Position, self.Geräteart, self.SB, self.VSU, self.Klauseln, self.Hersteller_Modul,\
            self.Hersteller_Wechselrichter, self.Leistung, self.Baujahr, self.Stand, self.Anzahl =\
                Position, Geräteart, SB, VSU, Klauseln, Hersteller_Modul, Hersteller_Wechselrichter, Leistung, Baujahr, Stand, Anzahl
            self.last_index = last_index
        else:
            Position, Geräteart, SB, VSU, Klauseln, Hersteller_Modul, Hersteller_Wechselrichter, Leistung, Baujahr, Stand, Anzahl = \
                self.Position, self.Geräteart, self.SB, self.VSU, self.Klauseln, self.Hersteller_Modul, self.Hersteller_Wechselrichter, \
                self.Leistung, self.Baujahr, self.Stand, self.Anzahl
            last_index = self.last_index
            kw = self.kw
            position_word = df[df['text'].str.contains('Posi-')]
            assert (len(position_word) == 1)
            left_posi, top_posi = list(position_word['left'])[0], list(position_word['top'])[0]
            top_horizontal_line = list(df[(df['top'] > top_posi) & (df['text'] == "<LINE>")]['top'])[2]  # find top_coordinate of horizontal line from table
            df_table = df[(df['top'] > top_posi) & (df['top'] < top_horizontal_line)]  # whole table
            df_number_position = df_table[
                (df_table['left'] > left_posi - 40) & (df_table['left'] < left_posi + 40)]  # number column
            number_pos = list(df_number_position[df_number_position['text'].str.contains('^\d{,2}$')]['text'])

            # ------- continues from previous page
            top_horizontal_line_1 = list(df[(df['top'] > top_posi) & (df['text'] == "<LINE>")]['top'])[1]
            if number_pos:
                top_number = list(df_number_position[df_number_position['text'] == number_pos[0]]['top'])[0]
                df_number = df_table[(df_table['top'] < top_number - 20) & (df_table['top'] > top_horizontal_line_1 - 20)]
            else:
                df_number = df_table[(df_table['top'] > top_horizontal_line_1 - 20) & (df_table['top'] < top_horizontal_line - 20)]
            df_block_group = tuple(df_number.groupby('block'))
            for blk_id, df_blk in df_block_group:
                    df_blk = find_lines(df_blk)
                    # -------------------------- Hersteller_Modul
                    if len(df_blk[df_blk['text'].str.contains("Modul")]) and len(
                            df_blk[df_blk['text'].str.contains('Hersteller')]):
                        tmp_Modul_line = list(df_blk.query('text.str.contains("Modul")')['line'])
                        if len(tmp_Modul_line) == 1:
                            tmp_Modul_line = tmp_Modul_line[0]
                            tmp_Hersteller_Modul = ' '.join(df_blk[df_blk["line"] == tmp_Modul_line]['text'])
                            tmp = re.split('Module', tmp_Hersteller_Modul)[1]
                            pattern = re.compile(r'^\W')
                            tmp = re.sub(pattern, '', tmp)
                            if len(tmp) > 2:
                                Hersteller_Modul[last_index] = tmp
                            else:
                                tmp_Modul_line += 1
                                Hersteller_Modul[last_index] = ' '.join(df_blk[df_blk['line'] == tmp_Modul_line]['text'])

                    # -------------------------- Hersteller_Wechselrichter
                    if len(df_blk[df_blk['text'].str.contains("Wechselrichter")]) and len(
                            df_blk[df_blk['text'].str.contains('Hersteller')]):
                        tmp_Wechselrichter_line = list(df_blk.query('text.str.contains("Wechselrichter")')['line'])
                        if len(tmp_Wechselrichter_line) == 1:
                            tmp_Wechselrichter_line = tmp_Wechselrichter_line[0]
                            tmp_Wechselrichter = ' '.join(df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                            tmp = re.split('Wechselrichter', tmp_Wechselrichter)[1]
                            tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                            if len(tmp) > 2:
                                Hersteller_Wechselrichter[last_index] = tmp
                            else:
                                tmp_Wechselrichter_line += 1
                                Hersteller_Wechselrichter[last_index] = ' '.join(df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                    # -------------------------- Baujahr
                    tmp_Baujahr_line = list(set(df_blk.query('text.str.contains("Baujahr")')['line']))
                    if len(tmp_Baujahr_line) == 1:
                        tmp_Baujahr_line = tmp_Baujahr_line[0]
                        tmp_Baujahr = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])
                        tmp = re.split('Baujahr', tmp_Baujahr)[1]
                        tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                        if len(tmp) > 2:
                            Baujahr[last_index] = tmp
                        else:
                            tmp_Baujahr_line += 1
                            Baujahr[last_index] = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])

                    #  ------------------------- Leistung section
                    tmp_Leistung_line = list(set(df_blk.query('text.str.contains("Nennleistung")')['line']))
                    if len(tmp_Leistung_line) == 1:
                        tmp_Leistung_line = tmp_Leistung_line[0]
                        tmp_Leistung = ' '.join(df_blk.query('line == @tmp_Leistung_line')['text'])
                        tmp = re.split('Nennleistung', tmp_Leistung)[1]
                        pattern = re.compile(r'^\W')
                        tmp = re.sub(pattern, '', tmp)
                        if len(tmp) > 2:
                            Leistung[last_index] = tmp
                        else:
                            tmp_Leistung_line += 1
                            Leistung[last_index] = ' '.join(df_blk.query('line = @tmp_Leistung_line')['text'])
            if not number_pos:
                self.Position, self.Geräteart, self.SB, self.VSU, self.Klauseln, self.Hersteller_Modul, \
                self.Hersteller_Wechselrichter, self.Leistung, self.Baujahr, self.Stand, self.Anzahl = \
                    Position, Geräteart, SB, VSU, Klauseln, Hersteller_Modul, Hersteller_Wechselrichter, Leistung, Baujahr, Stand, Anzahl

                kw['Position'], kw['Geräteart'], kw['SB'], kw['VSU'], kw['Klauseln'], kw['Hersteller Modul'], kw[
                    'Hersteller Wechselrichter'], \
                kw['Leistung'], kw['Baujahr'], kw['Stand'], kw[
                    'Anzahl'] = Position, Geräteart, SB, VSU, Klauseln, Hersteller_Modul, Hersteller_Wechselrichter, Leistung, Baujahr, Stand, Anzahl
                self.kw = kw
                return kw

            # --------- new positions -----------
            Position.extend(['None'] * len(number_pos)), Geräteart.extend(['None'] * len(number_pos)), SB.extend(
                ['None'] * len(number_pos)), \
            VSU.extend(['None'] * len(number_pos)), Klauseln.extend(['None'] * len(number_pos)), \
            Hersteller_Modul.extend(['None'] * len(number_pos)), Hersteller_Wechselrichter.extend(
                ['None'] * len(number_pos)), Leistung.extend(['None'] * len(number_pos)), Baujahr.extend(
                ['None'] * len(number_pos)), Stand.extend(['None'] * len(number_pos)), Anzahl.extend(
                ['None'] * len(number_pos))
            for m in range(len(number_pos) - 1):
                Position[m] = number_pos[m]
                top_number = list(df_number_position[df_number_position['text'] == number_pos[m]]['top'])[0]
                top_next_number = list(df_number_position[df_number_position['text'] == number_pos[m + 1]]['top'])[0]
                df_number = df_table[
                    (df_table['top'] > top_number - 20) & (df_table['top'] < top_next_number - 20)]  # Whole row
                # ------ Geräteart, VSU and SB column
                df_line_pos = df_number[(df_number['top'] < top_number + 50) & (df_number['top'] > top_number - 5)]
                text_line_pos = df_line_pos.query("text.str.contains('\d{2}') | text.str.contains('[a-zA-Z]')")
                Geräteart[-1] = text_line_pos.iloc[0]['text']
                left_summe = list(df_table.query('text.str.contains("summe")')['left'])
                if len(left_summe) == 1:
                    left_summe = left_summe[0]
                    text_line_pos = text_line_pos[(text_line_pos['left'] > left_summe - 60)]
                    VSU[-1] = text_line_pos.iloc[0]['text']
                    SB[-1] = text_line_pos.iloc[1]['text']

                df_block_group = tuple(df_number.groupby('block'))
                for blk_id, df_blk in df_block_group:
                    df_blk = find_lines(df_blk)
                    # -------------------------- Hersteller_Modul
                    if len(df_blk[df_blk['text'].str.contains("Modul")]) and len(
                            df_blk[df_blk['text'].str.contains('Hersteller')]):
                        tmp_Modul_line = list(set(df_blk.query('text.str.contains("Modul")')['line']))
                        if len(tmp_Modul_line) == 1:
                            tmp_Modul_line = tmp_Modul_line[0]
                            tmp_Hersteller_Modul = ' '.join(df_blk[df_blk["line"] == tmp_Modul_line]['text'])
                            tmp = re.split('Module', tmp_Hersteller_Modul)[1]
                            pattern = re.compile(r'^\W')
                            tmp = re.sub(pattern, '', tmp)
                            if len(tmp) > 2:
                                Hersteller_Modul[m] = tmp
                            else:
                                tmp_Modul_line += 1
                                Hersteller_Modul[m] = ' '.join(df_blk[df_blk['line'] == tmp_Modul_line]['text'])

                    # -------------------------- Hersteller_Wechselrichter
                    if len(df_blk[df_blk['text'].str.contains("Wechselrichter")]) and len(
                            df_blk[df_blk['text'].str.contains('Hersteller')]):
                        tmp_Wechselrichter_line = list(set(df_blk.query('text.str.contains("Wechselrichter")')['line']))
                        if len(tmp_Wechselrichter_line) == 1:
                            tmp_Wechselrichter_line = tmp_Wechselrichter_line[0]
                            tmp_Wechselrichter = ' '.join(df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                            tmp = re.split('Wechselrichter', tmp_Wechselrichter)[1]
                            tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                            if len(tmp) > 2:
                                Hersteller_Wechselrichter[m] = tmp
                            else:
                                tmp_Wechselrichter_line += 1
                                Hersteller_Wechselrichter[m] = ' '.join(df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                    # -------------------------- Baujahr
                    tmp_Baujahr_line = list(set(df_blk.query('text.str.contains("Baujahr")')['line']))
                    if len(tmp_Baujahr_line) == 1:
                        tmp_Baujahr_line = tmp_Baujahr_line[0]
                        tmp_Baujahr = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])
                        tmp = re.split('Baujahr', tmp_Baujahr)[1]
                        tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                        if len(tmp) > 2:
                            Baujahr[m] = tmp
                        else:
                            tmp_Baujahr_line += 1
                            Baujahr[m] = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])

                    #  ------------------------- Leistung section
                    tmp_Leistung_line = list(set(df_blk.query('text.str.contains("Nennleistung")')['line']))
                    if len(tmp_Leistung_line) == 1:
                        tmp_Leistung_line = tmp_Leistung_line[0]
                        tmp_Leistung = ' '.join(df_blk.query('line == @tmp_Leistung_line')['text'])
                        tmp = re.split('Nennleistung', tmp_Leistung)[1]
                        pattern = re.compile(r'^\W')
                        tmp = re.sub(pattern, '', tmp)
                        if len(tmp) > 2:
                            Leistung[m] = tmp
                        else:
                            tmp_Leistung_line += 1
                            Leistung[m] = ' '.join(df_blk.query('line = @tmp_Leistung_line')['text'])

            # ---------- last position of table
            Position[-1] = number_pos[-1]
            top_number = list(df_number_position[df_number_position['text'] == number_pos[-1]]['top'])[0]
            df_number = df_table[df_table['top'] > top_number - 20]  # Whole row
            # ------ Geräteart, VSU and SB column
            df_line_pos = df_number[(df_number['top'] < top_number + 50) & (df_number['top'] > top_number - 5)]
            text_line_pos = df_line_pos.query("text.str.contains('\d{2}') | text.str.contains('[a-zA-Z]')")
            Geräteart[-1] = text_line_pos.iloc[0]['text']
            left_summe = list(df_table.query('text.str.contains("summe")')['left'])
            if len(left_summe) == 1:
                left_summe = left_summe[0]
                text_line_pos = text_line_pos[(text_line_pos['left'] > left_summe - 60)]
                VSU[-1] = text_line_pos.iloc[0]['text']
                SB[-1] = text_line_pos.iloc[1]['text']

            df_block_group = tuple(df_number.groupby('block'))
            for blk_id, df_blk in df_block_group:
                df_blk = find_lines(df_blk)
                # -------------------------- Hersteller_Modul
                if len(df_blk[df_blk['text'].str.contains("Modul")]) and len(
                        df_blk[df_blk['text'].str.contains('Hersteller')]):
                    tmp_Modul_line = list(set(df_blk.query('text.str.contains("Modul")')['line']))
                    if len(tmp_Modul_line) == 1:
                        tmp_Modul_line = tmp_Modul_line[0]
                        tmp_Hersteller_Modul = ' '.join(df_blk[df_blk["line"] == tmp_Modul_line]['text'])
                        tmp = re.split('Module', tmp_Hersteller_Modul)[1]
                        pattern = re.compile(r'^\W')
                        tmp = re.sub(pattern, '', tmp)
                        if len(tmp) > 2:
                            Hersteller_Modul[-1] = tmp
                        else:
                            tmp_Modul_line += 1
                            Hersteller_Modul[-1] = ' '.join(df_blk[df_blk['line'] == tmp_Modul_line]['text'])

                # -------------------------- Hersteller_Wechselrichter
                if len(df_blk[df_blk['text'].str.contains("Wechselrichter")]) and len(
                        df_blk[df_blk['text'].str.contains('Hersteller')]):
                    tmp_Wechselrichter_line = list(set(df_blk.query('text.str.contains("Wechselrichter")')['line']))
                    if len(tmp_Wechselrichter_line) == 1:
                        tmp_Wechselrichter_line = tmp_Wechselrichter_line[0]
                        tmp_Wechselrichter = ' '.join(
                            df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                        tmp = re.split('Wechselrichter', tmp_Wechselrichter)[1]
                        tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                        if len(tmp) > 2:
                            Hersteller_Wechselrichter[-1] = tmp
                        else:
                            tmp_Wechselrichter_line += 1
                            Hersteller_Wechselrichter[-1] = ' '.join(
                                df_blk[df_blk['line'] == tmp_Wechselrichter_line]['text'])
                # -------------------------- Baujahr
                tmp_Baujahr_line = list(set(df_blk.query('text.str.contains("Baujahr")')['line']))
                if len(tmp_Baujahr_line) == 1:
                    tmp_Baujahr_line = tmp_Baujahr_line[0]
                    tmp_Baujahr = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])
                    tmp = re.split('Baujahr', tmp_Baujahr)[1]
                    tmp = re.sub('[^a-zA-Z0-9]', '', tmp)
                    if len(tmp) > 2:
                        Baujahr[-1] = tmp
                    else:
                        tmp_Baujahr_line += 1
                        Baujahr[-1] = ' '.join(df_blk[df_blk['line'] == tmp_Baujahr_line]['text'])

                #  ------------------------- Leistung section
                tmp_Leistung_line = list(set(df_blk.query('text.str.contains("Nennleistung")')['line']))
                if len(tmp_Leistung_line) == 1:
                    tmp_Leistung_line = tmp_Leistung_line[0]
                    tmp_Leistung = ' '.join(df_blk.query('line == @tmp_Leistung_line')['text'])
                    tmp = re.split('Nennleistung', tmp_Leistung)[1]
                    pattern = re.compile(r'^\W')
                    tmp = re.sub(pattern, '', tmp)
                    if len(tmp) > 2:
                        Leistung[-1] = tmp
                    else:
                        tmp_Leistung_line += 1
                        Leistung[-1] = ' '.join(df_blk.query('line = @tmp_Leistung_line')['text'])
            last_index += (len(number_pos) - 1)
            self.Position, self.Geräteart, self.SB, self.VSU, self.Klauseln, self.Hersteller_Modul, \
            self.Hersteller_Wechselrichter, self.Leistung, self.Baujahr, self.Stand, self.Anzahl = \
                Position, Geräteart, SB, VSU, Klauseln, Hersteller_Modul, Hersteller_Wechselrichter, Leistung, Baujahr, Stand, Anzahl
            self.last_index = last_index
        kw['Stand'] = stand
        kw['Position'], kw['Geräteart'], kw['SB'], kw['VSU'], kw['Klauseln'], kw['Hersteller Modul'], kw[
            'Hersteller Wechselrichter'], \
        kw['Leistung'], kw['Baujahr'], kw['Stand'], kw[
            'Anzahl'] = Position, Geräteart, SB, VSU, Klauseln, Hersteller_Modul, Hersteller_Wechselrichter, Leistung, Baujahr, Stand, Anzahl
        self.kw = kw
        return kw