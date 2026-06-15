"""Flask routes for viewing and managing the Alexa shopping list."""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash

from flaskapp import alexa_api

logger = logging.getLogger(__name__)

shopping_bp = Blueprint("shopping", __name__)


@shopping_bp.route("/")
def index():
    """Main page: shows the shopping list."""
    all_items = alexa_api.get_shopping_list_items()

    if all_items is None:
        flash("Could not retrieve shopping list. You may need to log in again.", "error")
        return render_template("shopping.html", incomplete_items=[], completed_items=[])

    incomplete_items = alexa_api.filter_incomplete_items(all_items)
    completed_items = [item for item in all_items if item.get("completed", False)]

    return render_template(
        "shopping.html",
        incomplete_items=incomplete_items,
        completed_items=completed_items,
    )


@shopping_bp.route("/items/add", methods=["POST"])
def add_item():
    """Adds a new item to the shopping list."""
    item_name = request.form.get("item_name", "").strip()
    if not item_name:
        flash("Item name cannot be empty.", "error")
        return redirect(url_for("shopping.index"))

    success = alexa_api.add_shopping_list_item(item_name)
    if success:
        flash(f"'{item_name}' added to your list.", "success")
    else:
        flash(f"Failed to add '{item_name}'. Please try again.", "error")

    return redirect(url_for("shopping.index"))


@shopping_bp.route("/items/delete", methods=["POST"])
def delete_item():
    """Deletes an item from the shopping list by name."""
    item_name = request.form.get("item_name", "").strip()
    if not item_name:
        flash("Item name cannot be empty.", "error")
        return redirect(url_for("shopping.index"))

    all_items = alexa_api.get_shopping_list_items()
    item = alexa_api.find_item_by_name(all_items or [], item_name)

    if not item:
        flash(f"'{item_name}' not found on your list.", "error")
        return redirect(url_for("shopping.index"))

    success = alexa_api.delete_shopping_list_item(item)
    if success:
        flash(f"'{item_name}' removed from your list.", "success")
    else:
        flash(f"Failed to remove '{item_name}'. Please try again.", "error")

    return redirect(url_for("shopping.index"))


@shopping_bp.route("/items/mark_completed", methods=["POST"])
def mark_completed():
    """Marks an item as completed."""
    item_name = request.form.get("item_name", "").strip()
    if not item_name:
        flash("Item name cannot be empty.", "error")
        return redirect(url_for("shopping.index"))

    all_items = alexa_api.get_shopping_list_items()
    incomplete_items = alexa_api.filter_incomplete_items(all_items or [])
    item = alexa_api.find_item_by_name(incomplete_items, item_name)

    if not item:
        flash(f"'{item_name}' not found in your active items.", "error")
        return redirect(url_for("shopping.index"))

    success = alexa_api.mark_item_as_completed(item)
    if success:
        flash(f"'{item_name}' marked as completed.", "success")
    else:
        flash(f"Failed to mark '{item_name}' as completed. Please try again.", "error")

    return redirect(url_for("shopping.index"))


@shopping_bp.route("/items/mark_incomplete", methods=["POST"])
def mark_incomplete():
    """Marks a completed item as incomplete."""
    item_name = request.form.get("item_name", "").strip()
    if not item_name:
        flash("Item name cannot be empty.", "error")
        return redirect(url_for("shopping.index"))

    all_items = alexa_api.get_shopping_list_items()
    completed_items = [item for item in (all_items or []) if item.get("completed", False)]
    item = alexa_api.find_item_by_name(completed_items, item_name)

    if not item:
        flash(f"'{item_name}' not found in your completed items.", "error")
        return redirect(url_for("shopping.index"))

    success = alexa_api.unmark_item_as_completed(item)
    if success:
        flash(f"'{item_name}' moved back to your active list.", "success")
    else:
        flash(f"Failed to update '{item_name}'. Please try again.", "error")

    return redirect(url_for("shopping.index"))

@shopping_bp.route("/items/clear_completed", methods=["POST"])
def clear_completed():
    all_items = alexa_api.get_shopping_list_items()

    if all_items is None:
        flash("Could not retrieve shopping list.", "error")
        return redirect(url_for("shopping.index"))

    completed_items = [item for item in all_items if item.get("completed", False)]

    if not completed_items:
        flash("No completed items to clear.", "info")
        return redirect(url_for("shopping.index"))

    deleted = 0

    for item in completed_items:
        # ✅ re-fetch via the same working path
        fresh_item = alexa_api.find_item_by_name(all_items, item["value"])

        if fresh_item and alexa_api.delete_shopping_list_item(fresh_item):
            deleted += 1

    if deleted:
        flash(f"Cleared {deleted} completed items.", "success")
    else:
        flash("No items were removed. Something may be wrong.", "warning")

    return redirect(url_for("shopping.index"))
