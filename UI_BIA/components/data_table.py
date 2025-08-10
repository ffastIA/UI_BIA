import reflex as rx
import pandas as pd
from typing import Optional, List


def create_data_table(df: Optional[pd.DataFrame], title: str) -> rx.Component:
    """Cria uma tabela de dados a partir de um DataFrame"""

    if df is None or df.empty:
        return rx.vstack(
            rx.heading(title, size="6"),
            rx.text("Nenhum dado disponível", color="gray"),
            spacing="4",
            width="100%"
        )

    # Limita a exibição a 50 linhas para performance
    display_df = df.head(50)

    # Converte DataFrame para lista de dicionários
    data = display_df.to_dict('records')
    columns = list(display_df.columns)

    return rx.vstack(
        rx.heading(title, size="6"),
        rx.text(f"Exibindo {len(display_df)} de {len(df)} registros", color="gray", size="2"),
        rx.data_table(
            data=data,
            columns=columns,
            pagination=True,
            search=True,
            sort=True,
        ),
        spacing="4",
        width="100%"
    )