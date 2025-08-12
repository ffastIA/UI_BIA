import reflex as rx
from typing import List, Dict


def create_data_table(data: List[Dict], columns: List[str], title: str) -> rx.Component:
    """Cria uma tabela de dados simples"""

    if not data or not columns:
        return rx.vstack(
            rx.heading(title, size="6"),
            rx.text("Nenhum dado disponível", color="gray"),
            spacing="4",
            width="100%"
        )

    # Cabeçalho da tabela
    header_cells = [rx.table.column_header_cell(col) for col in columns]

    # Linhas da tabela
    rows = []
    for row_data in data:
        cells = []
        for col in columns:
            value = row_data.get(col, "")
            # Converte para string e limita o tamanho
            cell_value = str(value)[:50] + ("..." if len(str(value)) > 50 else "")
            cells.append(rx.table.cell(cell_value))
        rows.append(rx.table.row(*cells))

    return rx.vstack(
        rx.heading(title, size="6"),
        rx.text(f"Exibindo {len(data)} registros", color="gray", size="2"),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(*header_cells)
                ),
                rx.table.body(*rows),
                variant="surface",
                size="1"
            ),
            width="100%",
            overflow_x="auto"
        ),
        spacing="4",
        width="100%"
    )