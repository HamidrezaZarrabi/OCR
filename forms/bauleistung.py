def find_values(main_dict, pdf_name):
    df_list = list(main_dict['dfs'].values())
    kw = {'Versicherungsschein': None}
    for i, dff in enumerate(df_list):
        df = dff.copy()
        line_Versicherungsschein = list(df[df['text'].str.contains('Versicherungsschein')]['line'])
        if len(line_Versicherungsschein) == 1:
            text_Versicherungsschein = list(df[df['line'] == line_Versicherungsschein[0]]['text'])
            kw['Versicherungsschein'] = text_Versicherungsschein[1]

        line_Ausfertigungsgrund = list(df[df['text'].str.contains('Ausfertigungsgrund')]['line'])
