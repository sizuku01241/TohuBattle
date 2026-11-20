"""アイテム一覧の選択とUndo/RedoをUIから分離した状態管理。"""

from __future__ import annotations

import copy

from .models import Item, item_from_dict, item_to_dict


class EditorState:
    def __init__(self, items: list[Item]):
        self.items = items
        self.selected_index: int | None = 0 if items else None
        self.undo_stack: list[list[dict]] = []
        self.redo_stack: list[list[dict]] = []

    @property
    def selected(self) -> Item | None:
        if self.selected_index is None or not 0 <= self.selected_index < len(self.items):
            return None
        return self.items[self.selected_index]

    def select(self, index: int | None) -> Item | None:
        if index is None or not 0 <= index < len(self.items):
            self.selected_index = None
        else:
            self.selected_index = index
        return self.selected

    def select_item(self, item: Item | None) -> Item | None:
        return self.select(self.items.index(item) if item in self.items else None)

    def snapshot(self) -> list[dict]:
        return copy.deepcopy([item_to_dict(item) for item in self.items])

    def replace(self, data: list[dict]) -> Item | None:
        self.items[:] = [item_from_dict(raw) for raw in copy.deepcopy(data)]
        if not self.items:
            self.selected_index = None
        elif self.selected_index is None:
            self.selected_index = 0
        else:
            self.selected_index = min(self.selected_index, len(self.items) - 1)
        return self.selected

    def record_change(self, before: list[dict]) -> None:
        if before == self.snapshot():
            return
        self.undo_stack.append(copy.deepcopy(before))
        self.redo_stack.clear()

    def undo(self) -> Item | None:
        if not self.undo_stack:
            return self.selected
        self.redo_stack.append(self.snapshot())
        return self.replace(self.undo_stack.pop())

    def redo(self) -> Item | None:
        if not self.redo_stack:
            return self.selected
        self.undo_stack.append(self.snapshot())
        return self.replace(self.redo_stack.pop())

    def remove_selected(self) -> Item | None:
        if self.selected_index is None or not 0 <= self.selected_index < len(self.items):
            return None
        self.items.pop(self.selected_index)
        if not self.items:
            self.selected_index = None
        else:
            self.selected_index = min(self.selected_index, len(self.items) - 1)
        return self.selected
