import reflex as rx
import pandas as pd
from typing import Optional, List, Dict, Any

from .services.sheets_service import SheetsService
from .components.sidebar import create_sidebar


class State(rx.State):
    """Estado da aplicação"""

    # Dados simplificados para exibição
    biometria_summary: str = ""
    racao_summary: str = ""

    # Dados das primeiras linhas para preview
    biometria_preview: List[List[str]] = []
    racao_preview: List[List[str]] = []

    # Cabeçalhos das tabelas
    biometria_headers: List[str] = []
    racao_headers: List[str] = []

    # Estados de carregamento
    is_loading: bool = False
    load_message: str = ""
    has_data: bool = False

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
                self.biometria_headers = [str(col) for col in biometria_df.columns]

                # Pega apenas as primeiras 10 linhas para preview
                preview_df = biometria_df.head(10)
                self.biometria_preview = []

                for _, row in preview_df.iterrows():
                    row_data = []
                    for value in row.values:
                        # Converte para string e limita tamanho
                        str_val = str(value) if pd.notna(value) else ""
                        if len(str_val) > 20:
                            str_val = str_val[:20] + "..."
                        row_data.append(str_val)
                    self.biometria_preview.append(row_data)

                self.biometria_summary = f"Total de {len(biometria_df)} registros, {len(biometria_df.columns)} colunas"
                messages.append(f"Biometria: {len(biometria_df)} registros")

            # Processa dados de Ração
            if racao_df is not None and not racao_df.empty:
                self.racao_headers = [str(col) for col in racao_df.columns]

                # Pega apenas as primeiras 10 linhas para preview
                preview_df = racao_df.head(10)
                self.racao_preview = []

                for _, row in preview_df.iterrows():
                    row_data = []
                    for value in row.values:
                        # Converte para string e limita tamanho
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


def index() -> rx.Component:
    """Página principal"""

    return rx.hstack(
        # Barra lateral
        create_sidebar(State.load_sheets_data),

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
                    ~State.has_data,
                    rx.center(
                        rx.vstack(
                            rx.icon("database", size=64, color=rx.color("gray", 6)),
                            rx.heading("Bem-vindo ao Aquicultura Analytics Pro", size="6", color=rx.color("gray", 8)),
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
                        # Tabela Biometria
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

                        # Tabela Ração
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