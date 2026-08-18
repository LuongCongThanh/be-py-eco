import pytest

from modules.catalog.errors import CategoryCycleError
from modules.catalog.services.category_tree import create_category, reparent_category


@pytest.mark.django_db
def test_create_category_without_parent() -> None:
    root = create_category()

    assert root.parent is None


@pytest.mark.django_db
def test_create_category_under_parent() -> None:
    root = create_category()

    child = create_category(parent=root)

    assert child.parent_id == root.id


@pytest.mark.django_db
def test_category_cannot_be_its_own_parent() -> None:
    root = create_category()

    with pytest.raises(CategoryCycleError):
        reparent_category(category=root, new_parent=root)


@pytest.mark.django_db
def test_reparenting_under_own_descendant_raises_cycle_error() -> None:
    root = create_category()
    child = create_category(parent=root)
    grandchild = create_category(parent=child)

    with pytest.raises(CategoryCycleError):
        reparent_category(category=root, new_parent=grandchild)

    # the tree is unchanged after the rejected attempt
    root.refresh_from_db()
    assert root.parent is None


@pytest.mark.django_db
def test_reparenting_to_a_valid_new_parent_succeeds() -> None:
    root = create_category()
    other_root = create_category()
    child = create_category(parent=root)

    reparent_category(category=child, new_parent=other_root)

    child.refresh_from_db()
    assert child.parent_id == other_root.id


@pytest.mark.django_db
def test_deleting_a_parent_with_children_is_protected() -> None:
    from django.db.models import ProtectedError

    root = create_category()
    create_category(parent=root)

    with pytest.raises(ProtectedError):
        root.delete()
