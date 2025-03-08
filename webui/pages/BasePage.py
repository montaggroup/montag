from rio import Component, TextStyle, Spacer, Card, Row, Column, Container, PageView, Text


class BasePage(Component):
    def build(self) -> Component:
        return Column(
            Row(Text("Navbar"), min_height=3, margin_left=2, margin_right=2),
            PageView(grow_y=True, margin_top=1, margin_bottom=1, margin_left=2, margin_right=2),
            Row(Text("Footer"), min_height=3, margin_left=2, margin_right=2)
        )
