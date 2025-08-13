import reflex as rx
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import json

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
    is_calculating: bool = False

    # Métricas simplificadas para o State
    tank_metrics: List[List[str]] = []  # [tanque, peixes_medidos, area_media, racao_utilizada]
    general_metrics: List[str] = []  # [total_peixes, area_media_geral, total_racao]

    # Dados para a tabela de correlação temporal
    correlation_tank_data: List[
        List[str]] = []  # [tanque, area_inicial, area_final, variacao, crescimento%, racao_total, eficiencia]
    correlation_general_data: List[
        str] = []  # [total_variacao, total_racao, media_crescimento, eficiencia_geral, tanques]
    has_correlation_data: bool = False

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
        self.load_message = "Recalculando métricas para o período selecionado..."

        try:
            self.calculate_metrics()
            self.calculate_temporal_correlation()

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

            # Calcula correlação temporal
            self.calculate_temporal_correlation()

        except Exception as e:
            print(f"Erro ao calcular métricas: {e}")
            self.tank_metrics = []
            self.general_metrics = []

    def calculate_temporal_correlation(self):
        """Calcula correlação temporal entre crescimento de área e ração"""
        try:
            if not self.has_data:
                self.has_correlation_data = False
                return

            # Calcula correlação temporal
            correlation_data = MetricsService.calculate_temporal_correlation(
                self.biometria_df, self.racao_df, self.start_date, self.end_date
            )

            if not correlation_data:
                self.has_correlation_data = False
                self.correlation_tank_data = []
                self.correlation_general_data = []
                return

            # Converte dados por tanque para lista simples
            self.correlation_tank_data = []
            for tanque, data in correlation_data.items():
                if tanque == 'geral':
                    continue

                # Determina cor do crescimento baseado no valor
                crescimento_val = data.get('percentual_crescimento', 0)
                crescimento_str = f"{crescimento_val:.1f}%"

                tank_row = [
                    str(tanque),  # Tanque
                    f"{data.get('area_inicial', 0):.2f}",  # Área Inicial
                    f"{data.get('area_final', 0):.2f}",  # Área Final
                    f"{data.get('variacao_area', 0):.2f}",  # Variação
                    crescimento_str,  # Crescimento %
                    f"{data.get('racao_total', 0):.2f}",  # Ração Total
                    f"{data.get('eficiencia_crescimento', 0):.4f}"  # Eficiência
                ]
                self.correlation_tank_data.append(tank_row)

            # Converte dados gerais para lista simples
            if 'geral' in correlation_data:
                geral = correlation_data['geral']
                self.correlation_general_data = [
                    f"{geral.get('total_variacao_area', 0):.2f}",  # Total Variação Área
                    f"{geral.get('total_racao', 0):.2f}",  # Total Ração
                    f"{geral.get('media_crescimento_percentual', 0):.1f}%",  # Média Crescimento %
                    f"{geral.get('eficiencia_geral', 0):.4f}",  # Eficiência Geral
                    str(geral.get('tanques_analisados', 0))  # Tanques Analisados
                ]
            else:
                self.correlation_general_data = []

            self.has_correlation_data = len(self.correlation_tank_data) > 0

        except Exception as e:
            print(f"Erro ao calcular correlação temporal: {e}")
            self.has_correlation_data = False
            self.correlation_tank_data = []
            self.correlation_general_data = []


def create_metric_card(title: str, value: str, icon: str) -> rx.Component:
    """Cria um card de métrica com fonte menor e cor preta"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=16, color="black"),
                rx.text(
                    title,
                    size="1",
                    weight="bold",
                    color="black"
                ),
                spacing="2",
                align="center"
            ),
            rx.text(
                value,
                size="4",
                weight="bold",
                color="black"
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


def create_correlation_table() -> rx.Component:
    """Cria a tabela de correlação temporal"""
    return rx.box(
        rx.vstack(
            rx.heading(
                "📈 Correlação Temporal: Crescimento da Área vs Ração Utilizada",
                size="4",
                color="black"
            ),
            rx.cond(
                State.has_correlation_data,
                rx.vstack(
                    # Explicação da análise
                    rx.box(
                        rx.vstack(
                            rx.text(
                                "📊 Análise de Correlação Temporal",
                                size="2",
                                weight="bold",
                                color="black"
                            ),
                            rx.text(
                                "Esta análise mostra a relação entre o crescimento da área dos peixes ao longo do tempo e a quantidade de ração utilizada no período selecionado.",
                                color="black",
                                size="1"
                            ),
                            spacing="2"
                        ),
                        padding="1rem",
                        border="1px solid",
                        border_color=rx.color("blue", 4),
                        border_radius="8px",
                        bg=rx.color("blue", 1),
                        width="100%"
                    ),

                    # Tabela por tanque
                    rx.vstack(
                        rx.heading("📋 Análise por Tanque", size="3", color="black"),
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Tanque", style={"font_weight": "bold"}),
                                        rx.table.column_header_cell("Área Inicial", style={"font_weight": "bold"}),
                                        rx.table.column_header_cell("Área Final", style={"font_weight": "bold"}),
                                        rx.table.column_header_cell("Variação", style={"font_weight": "bold"}),
                                        rx.table.column_header_cell("Crescimento %", style={"font_weight": "bold"}),
                                        rx.table.column_header_cell("Ração Total (kg)", style={"font_weight": "bold"}),
                                        rx.table.column_header_cell("Eficiência*", style={"font_weight": "bold"})
                                    )
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        State.correlation_tank_data,
                                        lambda row: rx.table.row(
                                            rx.table.cell(f"Tanque {row[0]}",
                                                          style={"font_weight": "bold", "color": "black"}),
                                            rx.table.cell(row[1], style={"color": "black"}),
                                            rx.table.cell(row[2], style={"color": "black"}),
                                            rx.table.cell(row[3], style={"color": "black"}),
                                            # Corrigido: usando rx.cond() em vez do operador 'in'
                                            rx.table.cell(
                                                row[4],
                                                style=rx.cond(
                                                    row[4].contains("-"),
                                                    {"color": "red"},
                                                    {"color": "green"}
                                                )
                                            ),
                                            rx.table.cell(row[5], style={"color": "black"}),
                                            rx.table.cell(row[6], style={"color": "black"})
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
                        spacing="3",
                        width="100%"
                    ),

                    # Resumo geral
                    rx.cond(
                        State.correlation_general_data.length() > 0,
                        rx.vstack(
                            rx.heading("📊 Resumo Geral do Período", size="3", color="black"),
                            rx.hstack(
                                create_metric_card("Variação Total da Área", State.correlation_general_data[0],
                                                   "trending-up"),
                                create_metric_card("Ração Total Utilizada", f"{State.correlation_general_data[1]} kg",
                                                   "package"),
                                create_metric_card("Crescimento Médio", State.correlation_general_data[2], "percent"),
                                create_metric_card("Eficiência Geral", State.correlation_general_data[3], "zap"),
                                create_metric_card("Tanques Analisados", State.correlation_general_data[4], "database"),
                                spacing="3",
                                width="100%",
                                wrap="wrap"
                            ),
                            spacing="3",
                            width="100%"
                        )
                    ),

                    # Legenda
                    rx.box(
                        rx.vstack(
                            rx.text(
                                "📖 Legenda e Interpretação",
                                size="2",
                                weight="bold",
                                color="black"
                            ),
                            rx.vstack(
                                rx.text("• Área Inicial/Final: Área média dos peixes no início e fim do período",
                                        size="1", color="black"),
                                rx.text("• Variação: Diferença entre área final e inicial", size="1", color="black"),
                                rx.text("• Crescimento %: Percentual de crescimento da área no período", size="1",
                                        color="black"),
                                rx.text("• Ração Total: Quantidade total de ração utilizada no período", size="1",
                                        color="black"),
                                rx.text("• Eficiência*: Variação de área por kg de ração (maior = mais eficiente)",
                                        size="1", color="black"),
                                rx.text("• Cores: Verde = crescimento positivo, Vermelho = crescimento negativo",
                                        size="1", color="black"),
                                spacing="1",
                                align="start"
                            ),
                            spacing="2"
                        ),
                        padding="1rem",
                        border="1px solid",
                        border_color=rx.color("gray", 4),
                        border_radius="8px",
                        bg=rx.color("gray", 1),
                        width="100%"
                    ),

                    spacing="4",
                    width="100%"
                ),
                rx.vstack(
                    rx.text(
                        "⚠️ Dados insuficientes para análise de correlação temporal.",
                        color="black",
                        size="2",
                        weight="bold"
                    ),
                    rx.text(
                        "Para visualizar a correlação temporal, certifique-se de que:",
                        color="black",
                        size="2"
                    ),
                    rx.vstack(
                        rx.text("• Existem dados de biometria e ração no período selecionado", size="1", color="black"),
                        rx.text("• O período contém pelo menos 2 medições por tanque", size="1", color="black"),
                        rx.text("• Os tanques possuem dados válidos de área e ração", size="1", color="black"),
                        rx.text("• As datas de início e fim estão definidas", size="1", color="black"),
                        spacing="1",
                        align="start",
                        padding_left="1rem"
                    ),
                    spacing="2",
                    align="start"
                )
            ),
            spacing="3"
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
            color="black"
        ),

        # Filtros de Data com Botão de Recálculo
        rx.box(
            rx.vstack(
                rx.text(
                    "Filtros de Período",
                    size="3",
                    weight="bold",
                    color="black"
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Data Inicial",
                            size="1",
                            weight="bold",
                            color="black"
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
                            size="1",
                            weight="bold",
                            color="black"
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
                    size="4",
                    color="black"
                ),
                rx.foreach(
                    State.tank_metrics,
                    lambda tank_row: rx.vstack(
                        rx.heading(
                            f"Tanque {tank_row[0]}",
                            size="3",
                            color="black"
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
                    size="4",
                    color="black"
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

        # Tabela de Correlação Temporal
        create_correlation_table(),

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