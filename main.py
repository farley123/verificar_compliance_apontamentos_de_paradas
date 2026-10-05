from flet import DropdownOption, controls, value
from flet.controls import layout_control
from flet.controls.material import dropdown
from openpyxl.cell import read_only

from extracao_pnp_execucao import (
    extrair_linhas,
    extrair_parada_planejada_com_comentario_suspeito,
    extrair_pnp_reclassifica_para_pp,
    extrair_pnp_reclassifica_para_tempo_em_producao,
    extrair_pnp_reclassifica_para_tempo_ocioso,
    extrair_pp_reclassifica_para_tempo_ocioso,
    total_de_eventos_de_paradas,
    extrair_tempo_em_execucao_com_comentario,
    extrair_parada_tecnica_sem_amm,
    extrair_tempo_ocioso_com_comentario_suspeito
)

if __name__ == "__main__":
    import flet as ft

    def main(page: ft.Page):
        page.title = "Verificar reclassificações DMO"
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.scroll = None
        page.window.width = 1650
        page.window.resizable = False

        container_tabela = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

        # Instancia o ProgressBar (inicia invisível)
        progresso = ft.ProgressBar(visible=False, width=1400)

        # Controle de paginação
        TAMANHO_PAGINA = 100
        pagina_atual = 0
        df_global = None

        def criar_tabela_paginada(df, pagina: int) -> ft.DataTable:
            inicio = pagina * TAMANHO_PAGINA
            fim = inicio + TAMANHO_PAGINA
            df_fatia = df.iloc[inicio:fim]

            columns = [ft.DataColumn(ft.Text(col)) for col in df_fatia.columns]
            rows = [
                ft.DataRow(cells=[ft.DataCell(ft.Text(str(val))) for val in row])
                for _, row in df_fatia.iterrows()
            ]

            return ft.DataTable(
                columns=columns,
                rows=rows,
                border=ft.border.Border.all(1, ft.Colors.GREY_300),
                vertical_lines=ft.border.Border.all(0.5, ft.Colors.GREY_200),
                horizontal_lines=ft.border.Border.all(0.5, ft.Colors.GREY_200),
            )

        lbl_pagina = ft.Text("Página 1")

        def mudar_pagina(delta: int):
            nonlocal pagina_atual, df_global
            if df_global is None:
                return

            total_paginas = (len(df_global) // TAMANHO_PAGINA) + (1 if len(df_global) % TAMANHO_PAGINA > 0 else 0)
            nova_pagina = pagina_atual + delta

            if 0 <= nova_pagina < total_paginas:
                pagina_atual = nova_pagina
                lbl_pagina.value = f"Página {pagina_atual + 1} de {total_paginas} ({len(df_global)} registros)"

                tabela = criar_tabela_paginada(df_global, pagina_atual)
                container_tabela.controls[0] = ft.Row(controls=[tabela], scroll=ft.ScrollMode.ALWAYS, expand=True)
                page.update()

        btn_anterior = ft.Button("Anterior", on_click=lambda e: mudar_pagina(-1))
        btn_proximo = ft.Button("Próximo", on_click=lambda e: mudar_pagina(1))
        controles_paginacao = ft.Row(
            controls=[btn_anterior, lbl_pagina, btn_proximo],
            alignment=ft.MainAxisAlignment.CENTER
        )

        def alternar_bloqueio_interface(bloquear: bool):
            progresso.visible = bloquear
            arquivo.disabled = bloquear
            dropdown_controle.disabled = bloquear
            radio_button.disabled = bloquear
            page.update()

        def calcular_horas_de_reclassificacao(quanty_reclassificado: float):
            horas = quanty_reclassificado / 60
            horas_de_reclassificação.value = f"{horas:.2f} horas"


        def executar_extracao(path: str, linha: str):
            progresso.visible = True
            container_tabela.controls.clear()
            horas_de_reclassificação.value=''
            total_de_eventos_periodo_selecionado.value=''
            page.update()
            alternar_bloqueio_interface(True)

            def rodar_em_background():
                linha_f = None if linha == "TODAS AS LINHAS" else linha

                if radio_button.value == "pnp_execucao":
                    df_resultado = extrair_pnp_reclassifica_para_tempo_em_producao(
                        path, linha_f
                    )
                elif radio_button.value =='pnp_pp':
                    df_resultado = extrair_pnp_reclassifica_para_pp(path, linha_f)
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

                total_de_eventos = total_de_eventos_de_paradas(path)
                eventos_reclassificados = float(df_resultado[1])
                horas_reclassificadas = df_resultado[2]

                def atualizar_ui():
                    nonlocal df_global, pagina_atual
                    df_global = df_resultado[0]
                    pagina_atual = 0

                    total_paginas = (len(df_global) // TAMANHO_PAGINA) + (
                        1 if len(df_global) % TAMANHO_PAGINA > 0 else 0)
                    lbl_pagina.value = f"Página 1 de {total_paginas} ({len(df_global)} registros filtrados)"

                    tabela = criar_tabela_paginada(df_global, pagina_atual)

                    container_tabela.controls.clear()
                    container_tabela.controls.append(
                        ft.Row(controls=[tabela], scroll=ft.ScrollMode.ALWAYS, expand=True)
                    )
                    container_tabela.controls.append(controles_paginacao)

                    calcular_horas_de_reclassificacao(horas_reclassificadas)
                    total_de_eventos_periodo_selecionado.value=total_de_eventos
                    progresso.visible = False
                    page.update()
                    alternar_bloqueio_interface(False)

                page.run_thread(atualizar_ui)

            page.run_thread(rodar_em_background)

        # SELEÇÃO E CARREGAMENTO DA PLANILHA EM SEGUNDO PLANO
        async def handle_save_file(e):
            horas_de_reclassificação.value=''
            total_de_eventos_periodo_selecionado.value=''
            container_tabela.controls.clear()
            dropdown_controle.value=''
            picker = ft.FilePicker()
            page.services.append(picker)

            files = await picker.pick_files(
                dialog_title="Selecione a planilha",
                allowed_extensions=["xlsx", "xls"],
            )
            if files:
                caminho_arquivo = files[0].path
                arquivo.value = caminho_arquivo

                progresso.visible = True
                alternar_bloqueio_interface(True)
                page.update()

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
                        progresso.visible = False
                        alternar_bloqueio_interface(False)
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
                        dropdown_controle := ft.Dropdown(on_select=ao_mudar_dropdown,width=350),
                        horas_de_reclassificação := ft.TextField(
                            label="Tempo reclassificado em horas", read_only=True, width=200
                        ),
                        total_de_eventos_periodo_selecionado := ft.TextField(label="Total de eventos", read_only=True, width=200),
                        radio_button := ft.RadioGroup(
                            value="pnp_execucao",
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Radio(
                                                label='PNP/PP',value='pnp_pp'
                                            ),
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

                                        ]
                                    ),
                                    ft.Row(
                                        controls=[
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

                    ]
                ),
                progresso,
                container_tabela,
            ],
        )
        page.add(coluna)

    ft.run(main)