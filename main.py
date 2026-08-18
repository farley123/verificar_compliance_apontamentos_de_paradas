from flet import DropdownOption, controls, value
from flet.controls import layout_control
from flet.controls.material import dropdown
from openpyxl.cell import read_only

from extracao_pnp_execucao import (
    extrair_linhas,
    extrair_parada_planejada_com_comentario_suspeito,
    extrair_pnp_reclassifica_para_tempo_em_producao,
    extrair_pnp_reclassifica_para_tempo_ocioso,
    extrair_pp_reclassifica_para_tempo_ocioso,
    tempo_total_de_paradas,
    extrair_tempo_em_execucao_com_comentario,
    extrair_parada_tecnica_sem_amm,
    extrair_tempo_ocioso_com_comentario_suspeito
)

if __name__ == "__main__":
    import flet as ft


    def criar_tabela_flet(df) -> ft.DataTable:
        # cria o cabeçalho
        columns = [ft.DataColumn(ft.Text(col)) for col in df.columns]
        # cria as linhas
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
        page.scroll = None
        page.window.width = 1650
        page.window.resizable = False

        container_tabela = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

        # Instancia o ProgressBar (inicia invisível)
        progresso = ft.ProgressBar(visible=False, width=1400)

        def alternar_bloqueio_interface(bloquear: bool):
            progresso.visible = bloquear
            arquivo.disabled = bloquear
            dropdown_controle.disabled = bloquear
            radio_button.disabled = bloquear
            page.update()

        def calcular_porcentagem_de_reclassificacao(
                tempo_reclassificado: float, tempo_total: float
        ):
            if tempo_reclassificado > 0:
                porcentagem_de_reclassificacao.value = (
                    f"{str(round(tempo_reclassificado / tempo_total * 100))} %"
                )
            else:
                porcentagem_de_reclassificacao.value = " 0 %"

        def executar_extracao(path: str, linha: str):
            progresso.visible = True
            container_tabela.controls.clear()
            page.update()
            alternar_bloqueio_interface(True)
            def rodar_em_background():
                linha_f = None if linha == "TODAS AS LINHAS" else linha

                if radio_button.value == "pnp_execucao":
                    df_resultado = extrair_pnp_reclassifica_para_tempo_em_producao(
                        path, linha_f
                    )
                elif radio_button.value == "pnp_ocioso":
                    df_resultado = extrair_pnp_reclassifica_para_tempo_ocioso(
                        path, linha_f
                    )
                elif radio_button.value == "pp_ocioso":
                    df_resultado = extrair_pp_reclassifica_para_tempo_ocioso(
                        path, linha_f
                    )
                elif radio_button.value == "comentario_supeito_em_pp":
                    df_resultado = extrair_parada_planejada_com_comentario_suspeito(
                        path, linha_f
                    )
                elif radio_button.value == "tempo_em_execucao_com_comentario":
                    df_resultado = extrair_tempo_em_execucao_com_comentario(
                        path, linha_f
                    )
                elif radio_button.value == "parada_tcnica_sem_amm":
                    df_resultado = extrair_parada_tecnica_sem_amm(
                        path, linha_f
                    )
                elif radio_button.value == "tempo_ocioso_com_comentario_suspeito":
                    df_resultado = extrair_tempo_ocioso_com_comentario_suspeito(
                        path, linha_f
                    )
                else:
                    def cancelar():
                        progresso.visible = False
                        page.update()
                        alternar_bloqueio_interface(False)

                    page.run_thread(cancelar)
                    return

                tabela = criar_tabela_flet(df_resultado[0])
                tempo_total = float(tempo_total_de_paradas(path))
                tempo_reclassificado = float(df_resultado[1])

                def atualizar_ui():
                    container_tabela.controls.append(
                        ft.Row(controls=[tabela], scroll=ft.ScrollMode.ALWAYS,expand=True)
                    )
                    calcular_porcentagem_de_reclassificacao(
                        tempo_reclassificado, tempo_total
                    )
                    progresso.visible = False
                    page.update()
                    alternar_bloqueio_interface(False)

                page.run_thread(atualizar_ui)

            page.run_thread(rodar_em_background)

        # SELEÇÃO E CARREGAMENTO DA PLANILHA EM SEGUNDO PLANO
        async def handle_save_file(e):
            picker = ft.FilePicker()
            page.services.append(picker)

            files = await picker.pick_files(
                dialog_title="Selecione a planilha",
                allowed_extensions=["xlsx", "xls"],
            )
            if files:
                caminho_arquivo = files[0].path
                arquivo.value = caminho_arquivo

                # Exibe a barra de progresso imediatamente ao escolher o arquivo
                progresso.visible = True
                page.update()

                # Processa a leitura pesada das linhas em uma thread separada
                def carregar_linhas_background():
                    linhas_extraidas = extrair_linhas(caminho_arquivo)

                    def atualizar_dropdown_ui():
                        dropdown_controle.options = [
                            ft.DropdownOption(text=result, key=result)
                            for result in linhas_extraidas
                        ]
                        dropdown_controle.options.append(
                            DropdownOption(text="TODAS AS LINHAS", key="TODAS AS LINHAS")
                        )
                        # Oculta a barra de progresso e atualiza a tela
                        progresso.visible = False
                        page.update()

                    page.run_thread(atualizar_dropdown_ui)

                page.run_thread(carregar_linhas_background)

        def ao_mudar_dropdown(e):
            linha_selecionada = dropdown_controle.value
            if arquivo.value and linha_selecionada:
                executar_extracao(arquivo.value, linha_selecionada)

        def ao_mudar_radio_button(e):
            if arquivo.value and dropdown_controle.value:
                executar_extracao(arquivo.value, dropdown_controle.value)

        coluna = ft.Column(
            expand=True,
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        arquivo := ft.TextField(
                            on_click=handle_save_file,
                            read_only=True,
                            width=790,
                            label="Escolher planilha",
                        ),
                    ]
                ),
                linha := ft.Row(
                    controls=[
                        dropdown_controle := ft.Dropdown(on_select=ao_mudar_dropdown),
                        radio_button := ft.RadioGroup(
                            value="pnp_execucao",
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Radio(
                                                label="PNP/EXECUÇÃO", value="pnp_execucao"
                                            ),
                                            ft.Radio(
                                                label="PNP/TEMPO OCIOSO", value="pnp_ocioso"
                                            ),
                                            ft.Radio(
                                                label="PP/TEMPO OCIOSO", value="pp_ocioso"
                                            ),
                                        ]
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Radio(
                                                label="COMENTÁRIO SUSPEITO EM PP",
                                                value="comentario_supeito_em_pp",
                                            ),
                                            ft.Radio(
                                                label="TEMPO EM EXECUÇÃO COM COMENTARIO",
                                                value="tempo_em_execucao_com_comentario",
                                            ),
                                            ft.Radio(
                                                label="PARADA TÉCNICA SEM AMM",
                                                value="parada_tcnica_sem_amm",
                                            ),
                                            ft.Radio(
                                                label="TEMPO OCIOSO COM COMENTÁRIO SUSPEITO",
                                                value="tempo_ocioso_com_comentario_suspeito",
                                            ),
                                        ]
                                    )



                                ]
                            ),
                            on_change=ao_mudar_radio_button,
                        ),
                        porcentagem_de_reclassificacao := ft.TextField(
                            label="% de reclassificações", read_only=True,width=200
                        ),
                    ]
                ),
                progresso,
                container_tabela,
            ],
        )
        page.add(coluna)


    ft.run(main)