import reflex as rx


def create_sidebar(on_load_data) -> rx.Component:
    """Cria a barra lateral com configurações"""

    return rx.box(
        rx.vstack(
            rx.heading("Configurações", size="5"),

            rx.divider(),

            rx.vstack(
                rx.text("Dados", weight="bold", size="3"),
                rx.button(
                    "Carregar Planilhas",
                    on_click=on_load_data,
                    variant="solid",
                    color_scheme="blue",
                    width="100%"
                ),
                spacing="2",
                width="100%"
            ),

            rx.divider(),

            rx.vstack(
                rx.text("Análises", weight="bold", size="3"),
                rx.text("(Em desenvolvimento)", color="gray", size="2"),
                spacing="2",
                width="100%"
            ),

            spacing="4",
            width="100%"
        ),
        padding="1rem",
        width="250px",
        height="100vh",
        bg=rx.color("gray", 1),
        border_right=f"1px solid {rx.color('gray', 4)}"
    )