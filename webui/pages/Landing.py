from rio import Component, TextStyle, Spacer, Card, Row, Column, Container, PageView, Text


class Landing(Component):
    def build(self) -> Component:
        return Column(
            Text("Hallo, ich bin eine Text-Komponente, innerhalb einer Page-Komponente")
        )
