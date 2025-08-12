import reflex as rx


def create_sidebar(on_load_data) -> rx.Component:
    """Cria a barra lateral com configurações"""

    return rx.box(
        rx.vstack(
            # Logo/Título
            rx.vstack(
                rx.icon("activity", size=32, color=rx.color("blue", 9)),
                rx.heading("Analytics", size="4", color=rx.color("blue", 9)),
                spacing="2",
                align="center",
                padding_bottom="1rem"
            ),

            rx.divider(),

            # Seção de Dados
            rx.vstack(
                rx.hstack(
                    rx.icon("database", size=16),
                    rx.text("Dados", weight="bold", size="3"),
                    spacing="2",
                    align="center"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("download", size=16),
                        rx.text("Carregar Planilhas"),
                        spacing="2",
                        align="center"
                    ),
                    on_click=on_load_data,
                    variant="solid",
                    color_scheme="blue",
                    width="100%",
                    size="2"
                ),
                rx.text(
                    "Importa dados das planilhas Google Sheets",
                    color="gray",
                    size="1",
                    text_align="center"
                ),
                spacing="3",
                width="100%"
            ),

            rx.divider(),

            # Seção de Análises
            rx.vstack(
                rx.hstack(
                    rx.icon("bar_chart_3", size=16),
                    rx.text("Análises", weight="bold", size="3"),
                    spacing="2",
                    align="center"
                ),
                rx.text("Em desenvolvimento", color="gray", size="2", style={"font_style": "italic"}),
                spacing="2",
                width="100%"
            ),

            rx.spacer(),

            # Rodapé
            rx.vstack(
                rx.divider(),
                rx.text("v1.0.0", color="gray", size="1", text_align="center"),
                spacing="2",
                width="100%"
            ),

            spacing="4",
            width="100%",
            height="100%"
        ),
        padding="1.5rem",
        width="280px",
        height="100vh",
        bg=rx.color("gray", 1),
        border_right=f"2px solid {rx.color('gray', 4)}"
    )