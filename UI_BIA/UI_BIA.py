import reflex as rx
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from .services.sheets_service import SheetsService
from .services.metrics_service import MetricsService
from .components.sidebar import create_sidebar


class State(rx.State):
    """Estado da aplicação"""

    # Dados das planilhas (armazenados internamente)
    biometria_df: Optional[pd.DataFrame] = None
    racao_df: Optional[pd.DataFrame] = None

    # Dados simplificados para exibição
    biometria_summary: str = ""
    racao_summary: str = ""
    biometria_preview: List[List[str]] = []
    racao_preview: List[List[str]] = []
    biometria_headers: List[str] = []
    racao_headers: List[str] = []

    # Estados de carregamento
    is_loading: bool = False
    load_message: str = ""
    has_data: bool = False

    # Dashboard de métricas
    show_dashboard: bool = False
    start_date: str = ""
    end_date: str = ""
    is_calculating: bool = False  # Novo estado para o botão de recálculo

    # Métricas simplificadas para o State
    tank_metrics: List[List[str]] = []  # [tanque, peixes_medidos, area_media, racao_utilizada]
    general_metrics: List[str] = []  # [total_peixes, area_media_geral, total_racao]

    def load_sheets_data(self):
        """Carrega os dados das planilhas"""
        self.is_loading = True
        self.load_message = "Carregando dados das planilhas..."

        try:
            # Carrega os dados
            biometria_df, racao_df = SheetsService.load_all_sheets()

            messages = []

            # Processa dados de Biometria
            if biometria_df is not None and not biometria_df.empty:
                self.biometria_df = biometria_df
                self.biometria_headers = [str(col) for col in biometria_df.columns]

                # Preview das primeiras 10 linhas
                preview_df = biometria_df.head(10)
                self.biometria_preview = []

                for _, row in preview_df.iterrows():
                    row_data = []
                    for value in row.values:
                        str_val = str(value) if pd.notna(value) else ""
                        if len(str_val) > 20:
                            str_val = str_val[:20] + "..."
                        row_data.append(str_val)
                    self.biometria_preview.append(row_data)

                self.biometria_summary = f"Total de {len(biometria_df)} registros, {len(biometria_df.columns)} colunas"
                messages.append(f"Biometria: {len(biometria_df)} registros")

            # Processa dados de Ração
            if racao_df is not None and not racao_df.empty:
                self.racao_df = racao_df
                self.racao_headers = [str(col) for col in racao_df.columns]

                # Preview das primeiras 10 linhas
                preview_df = racao_df.head(10)
                self.racao_preview = []

                for _, row in preview_df.iterrows():
                    row_data = []
                    for value in row.values:
                        str_val = str(value) if pd.notna(value) else ""
                        if len(str_val) > 20:
                            str_val = str_val[:20] + "..."
                        row_data.append(str_val)
                    self.racao_preview.append(row_data)

                self.racao_summary = f"Total de {len(racao_df)} registros, {len(racao_df.columns)} colunas"
                messages.append(f"Ração: {len(racao_df)} registros")

            if messages:
                self.load_message = "Dados carregados: " + " | ".join(messages)
                self.has_data = True
            else:
                self.load_message = "Erro: Não foi possível carregar nenhuma planilha"
                self.has_data = False

        except Exception as e:
            self.load_message = f"Erro ao carregar dados: {str(e)}"
            self.has_data = False

        finally:
            self.is_loading = False

    def toggle_dashboard(self):
        """Alterna exibição do dashboard"""
        self.show_dashboard = not self.show_dashboard
        if self.show_dashboard and self.has_data:
            self.calculate_metrics()

    def set_start_date(self, value: str):
        """Define data inicial"""
        self.start_date = value

    def set_end_date(self, value: str):
        """Define data final"""
        self.end_date = value

    def recalculate_metrics(self):
        """Recalcula as métricas com base no período selecionado"""
        if not self.has_data:
            return

        if not self.start_date or not self.end_date:
            self.load_message = "Por favor, selecione as datas inicial e final para recalcular as métricas."
            return

        self.is_calculating = True

        # Converte datas para exibição na mensagem
        try:
            start_display = self.start_date
            end_display = self.end_date

            # Se as datas estão no formato ISO, converte para exibição
            if "-" in self.start_date:
                start_obj = datetime.strptime(self.start_date, "%Y-%m-%d")
                start_display = start_obj.strftime("%d/%m/%Y")

            if "-" in self.end_date:
                end_obj = datetime.strptime(self.end_date, "%Y-%m-%d")
                end_display = end_obj.strftime("%d/%m/%Y")

            self.load_message = f"Recalculando métricas para o período de {start_display} a {end_display}..."

        except:
            self.load_message = "Recalculando métricas para o período selecionado..."

        try:
            self.calculate_metrics()

            # Mensagem de sucesso com datas formatadas
            try:
                start_display = self.start_date
                end_display = self.end_date

                if "-" in self.start_date:
                    start_obj = datetime.strptime(self.start_date, "%Y-%m-%d")
                    start_display = start_obj.strftime("%d/%m/%Y")

                if "-" in self.end_date:
                    end_obj = datetime.strptime(self.end_date, "%Y-%m-%d")
                    end_display = end_obj.strftime("%d/%m/%Y")

                self.load_message = f"Métricas recalculadas para o período de {start_display} a {end_display}"
            except:
                self.load_message = "Métricas recalculadas com sucesso!"

        except Exception as e:
            self.load_message = f"Erro ao recalcular métricas: {str(e)}"
        finally:
            self.is_calculating = False

    def calculate_metrics(self):
        """Calcula métricas do dashboard"""
        if not self.has_data:
            return

        try:
            # Calcula métricas de biometria
            biometry_metrics = MetricsService.calculate_biometry_metrics(
                self.biometria_df, self.start_date, self.end_date
            )

            # Calcula métricas de ração
            feed_metrics = MetricsService.calculate_feed_metrics(
                self.racao_df, self.start_date, self.end_date
            )

            # Converte para listas simples para o State
            self.tank_metrics = []
            self.general_metrics = []

            # Métricas por tanque
            if biometry_metrics.get('por_tanque') and feed_metrics.get('por_tanque'):
                for tanque in biometry_metrics['por_tanque']:
                    bio_data = biometry_metrics['por_tanque'][tanque]
                    feed_data = feed_metrics['por_tanque'].get(tanque, {})

                    tank_row = [
                        str(tanque),
                        str(bio_data.get('peixes_medidos', 0)),
                        f"{bio_data.get('area_media', 0.0):.2f}",
                        f"{feed_data.get('racao_utilizada', 0.0):.2f}"
                    ]
                    self.tank_metrics.append(tank_row)

            # Métricas gerais
            if biometry_metrics.get('geral') and feed_metrics.get('geral'):
                self.general_metrics = [
                    str(biometry_metrics['geral'].get('total_peixes_medidos', 0)),
                    f"{biometry_metrics['geral'].get('area_media_geral', 0.0):.2f}",
                    f"{feed_metrics['geral'].get('total_racao_utilizada', 0.0):.2f}"
                ]

        except Exception as e:
            print(f"Erro ao calcular métricas: {e}")
            self.tank_metrics = []
            self.general_metrics = []


def create_metric_card(title: str, value: str, icon: str) -> rx.Component:
    """Cria um card de métrica com fonte menor e cor preta"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=16, color="black"),  # Ícone menor e preto
                rx.text(
                    title,
                    size="1",  # Fonte menor (era "2")
                    weight="bold",
                    color="green"  # Cor preta
                ),
                spacing="2",
                align="center"
            ),
            rx.text(
                value,
                size="4",  # Fonte menor (era "6")
                weight="bold",
                color="blue"  # Cor azul
            ),
            spacing="2",
            align="start"
        ),
        padding="1rem",
        border="1px solid",
        border_color=rx.color("gray", 4),
        border_radius="8px",
        bg=rx.color("gray", 1),
        width="100%"
    )


def create_dashboard() -> rx.Component:
    """Cria o dashboard de métricas"""
    return rx.vstack(
        # Cabeçalho do Dashboard
        rx.heading(
            "📊 Dashboard de Métricas",
            size="7",
            color="black"  # Cor preta
        ),

        # Filtros de Data com Botão de Recálculo
        rx.box(
            rx.vstack(
                rx.text(
                    "Filtros de Período",
                    size="3",  # Fonte menor (era "4")
                    weight="bold",
                    color="black"  # Cor preta
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Data Inicial",
                            size="1",  # Fonte menor (era "2")
                            weight="bold",
                            color="black"  # Cor preta
                        ),
                        rx.input(
                            placeholder="dd/mm/aaaa",
                            value=State.start_date,
                            on_change=State.set_start_date,
                            type="date",
                            size="2"
                        ),
                        spacing="1",
                        align="start"
                    ),
                    rx.vstack(
                        rx.text(
                            "Data Final",
                            size="1",  # Fonte menor (era "2")
                            weight="bold",
                            color="black"  # Cor preta
                        ),
                        rx.input(
                            placeholder="dd/mm/aaaa",
                            value=State.end_date,
                            on_change=State.set_end_date,
                            type="date",
                            size="2"
                        ),
                        spacing="1",
                        align="start"
                    ),
                    # Botão de Recálculo
                    rx.vstack(
                        rx.text(
                            "Ação",
                            size="1",
                            weight="bold",
                            color="black"
                        ),
                        rx.button(
                            rx.cond(
                                State.is_calculating,
                                rx.hstack(
                                    rx.spinner(size="3"),
                                    rx.text("Calculando...", size="1"),
                                    spacing="2",
                                    align="center"
                                ),
                                rx.hstack(
                                    rx.icon("calculator", size=16),
                                    rx.text("Recalcular", size="1"),
                                    spacing="2",
                                    align="center"
                                )
                            ),
                            on_click=State.recalculate_metrics,
                            variant="solid",
                            color_scheme="blue",
                            size="2",
                            disabled=State.is_calculating
                        ),
                        spacing="1",
                        align="start"
                    ),
                    spacing="4",
                    align="end"
                ),
                spacing="3"
            ),
            padding="1rem",
            border="1px solid",
            border_color=rx.color("gray", 4),
            border_radius="8px",
            bg=rx.color("gray", 1),
            width="100%"
        ),

        # Métricas por Tanque
        rx.cond(
            State.tank_metrics.length() > 0,
            rx.vstack(
                rx.heading(
                    "Métricas por Tanque",
                    size="4",  # Fonte menor (era "5")
                    color="black"  # Cor preta
                ),
                rx.foreach(
                    State.tank_metrics,
                    lambda tank_row: rx.vstack(
                        rx.heading(
                            f"Tanque {tank_row[0]}",
                            size="3",  # Fonte menor (era "4")
                            color="black"  # Cor preta
                        ),
                        rx.hstack(
                            create_metric_card("Peixes Medidos", tank_row[1], "fish"),
                            create_metric_card("Área Média", tank_row[2], "ruler"),
                            create_metric_card("Ração Utilizada", f"{tank_row[3]} kg", "package"),
                            spacing="4",
                            width="100%"
                        ),
                        spacing="3",
                        width="100%"
                    )
                ),
                spacing="4",
                width="100%"
            )
        ),

        # Métricas Gerais
        rx.cond(
            State.general_metrics.length() > 0,
            rx.vstack(
                rx.heading(
                    "Métricas Gerais",
                    size="4",  # Fonte menor (era "5")
                    color="black"  # Cor preta
                ),
                rx.hstack(
                    create_metric_card("Total Peixes Medidos", State.general_metrics[0], "fish"),
                    create_metric_card("Área Média Geral", State.general_metrics[1], "ruler"),
                    create_metric_card("Total Ração Utilizada", f"{State.general_metrics[2]} kg", "package"),
                    spacing="4",
                    width="100%"
                ),
                spacing="3",
                width="100%"
            )
        ),

        # Placeholder para gráfico de correlação
        rx.box(
            rx.vstack(
                rx.heading(
                    "Correlação: Área Média vs Ração por Tanque",
                    size="4",  # Fonte menor (era "5")
                    color="black"  # Cor preta
                ),
                rx.text(
                    "Gráfico de correlação será implementado na próxima versão",
                    color="black",  # Cor preta
                    size="2",  # Fonte menor
                    style={"font_style": "italic"}
                ),
                spacing="3"
            ),
            padding="1rem",
            border="1px solid",
            border_color=rx.color("gray", 4),
            border_radius="8px",
            bg=rx.color("gray", 1),
            width="100%"
        ),

        spacing="6",
        width="100%"
    )


def index() -> rx.Component:
    """Página principal"""

    return rx.hstack(
        # Barra lateral
        create_sidebar(State.load_sheets_data, State.toggle_dashboard),

        # Conteúdo principal
        rx.box(
            rx.vstack(
                # Cabeçalho
                rx.hstack(
                    rx.heading("Aquicultura Analytics Pro", size="8", color=rx.color("blue", 9)),
                    rx.spacer(),
                    rx.cond(
                        State.is_loading,
                        rx.hstack(
                            rx.spinner(size="3"),
                            rx.text("Carregando...", color="gray"),
                            spacing="2",
                            align="center"
                        ),
                    ),
                    width="100%",
                    align="center",
                    padding_bottom="1rem"
                ),

                # Mensagem de status
                rx.cond(
                    State.load_message != "",
                    rx.callout(
                        State.load_message,
                        icon="info",
                        size="1",
                        variant="soft"
                    ),
                ),

                # Conteúdo principal
                rx.cond(
                    State.show_dashboard & State.has_data,
                    create_dashboard(),
                    rx.cond(
                        ~State.has_data,
                        rx.center(
                            rx.vstack(
                                rx.icon("database", size=64, color=rx.color("gray", 6)),
                                rx.heading("Bem-vindo ao Aquicultura Analytics Pro", size="6",
                                           color=rx.color("gray", 8)),
                                rx.text(
                                    "Clique em 'Carregar Planilhas' na barra lateral para importar os dados das planilhas do Google Sheets.",
                                    color="gray",
                                    size="4",
                                    text_align="center",
                                    max_width="400px"
                                ),
                                spacing="4",
                                align="center"
                            ),
                            height="60vh",
                            width="100%"
                        ),
                        rx.vstack(
                            # Preview da Tabela Biometria
                            rx.cond(
                                State.biometria_headers.length() > 0,
                                rx.vstack(
                                    rx.heading("📊 Dados de Biometria", size="6"),
                                    rx.text(State.biometria_summary, color="gray", size="2"),
                                    rx.box(
                                        rx.table.root(
                                            rx.table.header(
                                                rx.table.row(
                                                    rx.foreach(
                                                        State.biometria_headers,
                                                        lambda header: rx.table.column_header_cell(header)
                                                    )
                                                )
                                            ),
                                            rx.table.body(
                                                rx.foreach(
                                                    State.biometria_preview,
                                                    lambda row: rx.table.row(
                                                        rx.foreach(
                                                            row,
                                                            lambda cell: rx.table.cell(cell)
                                                        )
                                                    )
                                                )
                                            ),
                                            variant="surface",
                                            size="1"
                                        ),
                                        width="100%",
                                        overflow_x="auto",
                                        border="1px solid",
                                        border_color=rx.color("gray", 4),
                                        border_radius="8px"
                                    ),
                                    spacing="4",
                                    width="100%"
                                )
                            ),

                            # Preview da Tabela Ração
                            rx.cond(
                                State.racao_headers.length() > 0,
                                rx.vstack(
                                    rx.heading("🍽️ Dados de Ração", size="6"),
                                    rx.text(State.racao_summary, color="gray", size="2"),
                                    rx.box(
                                        rx.table.root(
                                            rx.table.header(
                                                rx.table.row(
                                                    rx.foreach(
                                                        State.racao_headers,
                                                        lambda header: rx.table.column_header_cell(header)
                                                    )
                                                )
                                            ),
                                            rx.table.body(
                                                rx.foreach(
                                                    State.racao_preview,
                                                    lambda row: rx.table.row(
                                                        rx.foreach(
                                                            row,
                                                            lambda cell: rx.table.cell(cell)
                                                        )
                                                    )
                                                )
                                            ),
                                            variant="surface",
                                            size="1"
                                        ),
                                        width="100%",
                                        overflow_x="auto",
                                        border="1px solid",
                                        border_color=rx.color("gray", 4),
                                        border_radius="8px"
                                    ),
                                    spacing="4",
                                    width="100%"
                                )
                            ),

                            spacing="8",
                            width="100%"
                        )
                    )
                ),

                spacing="6",
                width="100%"
            ),
            padding="2rem",
            width="100%",
            height="100vh",
            overflow_y="auto"
        ),

        width="100%",
        height="100vh",
        spacing="0"
    )


# Configuração da aplicação
app = rx.App()
app.add_page(index, route="/", title="Aquicultura Analytics Pro")