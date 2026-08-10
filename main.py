from flet import controls, DropdownOption, value
from flet.controls import layout_control
from flet.controls.material import dropdown
from openpyxl.cell import read_only

from extracao_pnp_execucao import (extrair_pnp_reclassifica_para_tempo_em_producao,extrair_linhas,tempo_total_de_paradas,
                                   extrair_pnp_reclassifica_para_tempo_ocioso,extrair_pp_reclassifica_para_tempo_ocioso,
                                   extrair_parada_planejada_com_comentario_suspeito)

if __name__ == '__main__':
    import flet as ft
    def criar_tabela_flet(df)-> ft.DataTable:
        #cria o cabeçalho
        columns= [ft.DataColumn(ft.Text(col))for col in df.columns]
        #cria as linhas
        rows = []
        for _, row in df.iterrows():
            cells = [ft.DataCell(ft.Text(str(val))) for val in row]
            rows.append(ft.DataRow(cells=cells))
        return ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.Border.all(1, ft.Colors.GREY_300),
            vertical_lines=ft.border.Border.all(0.5, ft.Colors.GREY_200),
            horizontal_lines=ft.border.Border.all(0.5, ft.Colors.GREY_200),
        )



    def main(page: ft.Page):
        page.title = "Verificar reclassificações"
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.scroll=None
        page.window.width=1450
        page.window.resizable=False

        container_tabela = ft.Column(scroll=ft.ScrollMode.ALWAYS,expand=True)

        def calcular_porcentagem_de_reclassificacao(tempo_reclassificado:float,tempo_total:float):
            if tempo_reclassificado > 0:
                porcentagem_de_reclassificacao.value = f'{str(round(tempo_reclassificado / tempo_total * 100))} %'
            else:
                porcentagem_de_reclassificacao.value = f' 0 %'


        def executar_extracao(path:str,linha:str):
            if linha == 'TODAS AS LINHAS':
                linha=None
            if radio_button.value == 'pnp_execucao':
                df_resultado = extrair_pnp_reclassifica_para_tempo_em_producao(path, linha)
                tabela = criar_tabela_flet(df_resultado[0])
                container_tabela.controls.append(
                    ft.Row(
                        controls=[tabela],scroll=ft.ScrollMode.AUTO)
                )
                tempo_total=float(tempo_total_de_paradas(path))
                tempo_reclassificado=float(df_resultado[1])
                calcular_porcentagem_de_reclassificacao(tempo_reclassificado,tempo_total)
                page.update()
            if radio_button.value == 'pnp_ocioso':
                df_resultado = extrair_pnp_reclassifica_para_tempo_ocioso(path, linha)
                tabela = criar_tabela_flet(df_resultado[0])
                container_tabela.controls.append(
                    ft.Row(
                        controls=[tabela], scroll=ft.ScrollMode.AUTO)
                )
                tempo_total = float(tempo_total_de_paradas(path))
                tempo_reclassificado = float(df_resultado[1])
                calcular_porcentagem_de_reclassificacao(tempo_reclassificado, tempo_total)
                page.update()
            if radio_button.value == 'pp_ocioso':
                df_resultado = extrair_pp_reclassifica_para_tempo_ocioso(path, linha)
                tabela = criar_tabela_flet(df_resultado[0])
                container_tabela.controls.append(
                    ft.Row(
                        controls=[tabela], scroll=ft.ScrollMode.AUTO)
                )
                tempo_total = float(tempo_total_de_paradas(path))
                tempo_reclassificado = float(df_resultado[1])
                calcular_porcentagem_de_reclassificacao(tempo_reclassificado, tempo_total)
                page.update()

            if radio_button.value == 'comentario_supeito_em_pp':
                df_resultado = extrair_parada_planejada_com_comentario_suspeito(path, linha)
                tabela = criar_tabela_flet(df_resultado[0])
                container_tabela.controls.append(
                    ft.Row(
                        controls=[tabela], scroll=ft.ScrollMode.AUTO)
                )
                tempo_total = float(tempo_total_de_paradas(path))
                tempo_reclassificado = float(df_resultado[1])
                calcular_porcentagem_de_reclassificacao(tempo_reclassificado, tempo_total)
                page.update()

        async def handle_save_file(e):
            files = await ft.FilePicker().pick_files(dialog_title="Selecione a planilha",
            allowed_extensions=["xlsx", "xls"])
            if files:
                arquivo.value = files[0].path
                dropdown.options=[ft.DropdownOption(text=result,key=result) for result in extrair_linhas(arquivo.value)]
                dropdown.options.append(DropdownOption(text='TODAS AS LINHAS',key="TODAS AS LINHAS"))

                page.update()


        def ao_mudar_dropdown(e):
            # e.data contém a chave (key) do item selecionado
            linha_selecionada = e.data
            container_tabela.controls.clear()
            if arquivo.value and linha_selecionada:
                executar_extracao(arquivo.value, linha_selecionada)

        def ao_mudar_radio_button(e):
            container_tabela.controls.clear()
            if arquivo.value and dropdown.value:
                executar_extracao(arquivo.value, dropdown.value)

        coluna=ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    controls=[
                        arquivo:=ft.TextField(on_click= handle_save_file,read_only=True,width=790,label="Escolher planilha"),

                    ]
                ),
                linha:=ft.Row(
                    controls=[
                        dropdown:=ft.Dropdown(on_text_change=ao_mudar_dropdown),
                        radio_button:=ft.RadioGroup(
                            value="pnp_execucao",
                            content=ft.Row(
                                controls=[
                                    ft.Radio(label="PNP/EXECUÇÃO", value="pnp_execucao"),
                                    ft.Radio(label="PNP/TEMPO OCIOSO", value="pnp_ocioso"),
                                    ft.Radio(label="PP/TEMPO OCIOSO", value="pp_ocioso"),
                                    ft.Radio(label='COMENTÁRIO SUSPEITO EM PP',value='comentario_supeito_em_pp'),
                                ]
                            ),

                            on_change=ao_mudar_radio_button

                        ),
                        porcentagem_de_reclassificacao:=ft.TextField(label='% de reclassificações',read_only=True)
                    ]
                ),
                container_tabela


            ]
        )
        page.add(coluna)






    ft.run(main)