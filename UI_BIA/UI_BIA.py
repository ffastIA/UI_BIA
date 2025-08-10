import reflex as rx
import pandas as pd
from typing import Optional

from .services.sheets_service import SheetsService
from .components.sidebar import create_sidebar
from .components.data_table import create_data_table


class State(rx.State):
    """Estado da aplicação"""

    # DataFrames como strings JSON para serialização
    biometria_data: list[dict] = []
    racao_data: list[dict] = []

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

            if biometria_df is not None and not biometria_df.empty:
                self.biometria_data = biometria_df.head(50).to_dict('records')
                messages.append(f"Biometria: {len(biometria_df)} registros")

            if racao_df is not None and not racao_df.empty:
                self.racao_data = racao_df.head(50).to_dict('records')
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
                    rx.heading("Aquicultura Analytics Pro", size="8"),
                    rx.spacer(),
                    rx.cond(
                        State.is_loading,
                        rx.spinner(size="3"),
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
                        size="1"
                    ),
                ),

                # Conteúdo principal
                rx.cond(
                    ~State.has_data,
                    rx.center(
                        rx.text(
                            "Clique em 'Carregar Planilhas' na barra lateral para importar os dados.",
                            color="gray",
                            size="4",
                            text_align="center"
                        ),
                        height="50vh",
                        width="100%"
                    ),
                    rx.vstack(
                        # Tabela Biometria
                        rx.cond(
                            State.biometria_data.length() > 0,
                            rx.vstack(
                                rx.heading("Dados de Biometria", size="6"),
                                rx.data_table(
                                    data=State.biometria_data,
                                    pagination=True,
                                    search=True,
                                    sort=True,
                                ),
                                spacing="4",
                                width="100%"
                            )
                        ),

                        # Tabela Ração
                        rx.cond(
                            State.racao_data.length() > 0,
                            rx.vstack(
                                rx.heading("Dados de Ração", size="6"),
                                rx.data_table(
                                    data=State.racao_data,
                                    pagination=True,
                                    search=True,
                                    sort=True,
                                ),
                                spacing="4",
                                width="100%"
                            )
                        ),

                        spacing="6",
                        width="100%"
                    )
                ),

                spacing="4",
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