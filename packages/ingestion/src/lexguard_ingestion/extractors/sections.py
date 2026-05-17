import re

from lexguard_shared.schemas.document import DocumentSection

from lexguard_ingestion.models import SectionNode, TextBlock


class SectionExtractor:
    """Builds hierarchical sections from flat text blocks using font/level cues."""

    _NUMBERED_HEADING = re.compile(
        r"^(\d+\.)+\s+.+$|^[IVXLC]+\.\s+.+$|^(?:Chapter|Section|Article|Part)\s+\d+",
        re.IGNORECASE,
    )

    def from_blocks(self, blocks: list[TextBlock]) -> list[SectionNode]:
        if not blocks:
            return [SectionNode(title="Document", content="", page=1)]

        body_size = self._median_body_font(blocks)
        nodes: list[SectionNode] = []
        current: SectionNode | None = None
        stack: list[SectionNode] = []

        for block in blocks:
            text = block.text.strip()
            if not text:
                continue

            is_heading = self._is_heading(block, body_size)
            if is_heading:
                level = block.level if block.level > 0 else self._infer_level(block, body_size)
                node = SectionNode(title=text, page=block.page, level=level)

                while stack and stack[-1].level >= level:
                    stack.pop()

                if stack:
                    stack[-1].children.append(node)
                else:
                    nodes.append(node)

                stack.append(node)
                current = node
            elif current is not None:
                current.content = f"{current.content}\n{text}".strip() if current.content else text
            else:
                if not nodes:
                    nodes.append(SectionNode(title="Document", page=block.page, level=1))
                    stack.append(nodes[0])
                    current = nodes[0]
                current.content = f"{current.content}\n{text}".strip() if current.content else text

        return nodes or [SectionNode(title="Document", content="", page=blocks[0].page)]

    def to_schema(self, nodes: list[SectionNode]) -> list[DocumentSection]:
        return [self._node_to_section(node) for node in nodes]

    def _node_to_section(self, node: SectionNode) -> DocumentSection:
        return DocumentSection(
            title=node.title,
            content=node.content.strip(),
            page=node.page,
            subsections=[self._node_to_section(child) for child in node.children],
        )

    def _median_body_font(self, blocks: list[TextBlock]) -> float:
        sizes = sorted(b.font_size for b in blocks if b.font_size > 0)
        if not sizes:
            return 12.0
        return sizes[len(sizes) // 2]

    def _is_heading(self, block: TextBlock, body_size: float) -> bool:
        if block.level > 0:
            return True
        if block.is_bold and block.font_size >= body_size:
            return True
        if block.font_size > body_size * 1.15:
            return True
        text = block.text.strip()
        if len(text) < 120 and self._NUMBERED_HEADING.match(text):
            return True
        return bool(text.isupper() and len(text) < 80)

    def _infer_level(self, block: TextBlock, body_size: float) -> int:
        if block.level > 0:
            return block.level
        ratio = block.font_size / body_size if body_size else 1.0
        if ratio >= 1.8:
            return 1
        if ratio >= 1.4:
            return 2
        if ratio >= 1.15:
            return 3
        return 4
