# ================================================================
# SHARED CHART HELPER — adds data labels to bar / barh containers
# ================================================================

import matplotlib


def add_bar_labels(ax, fmt='{:,.0f}', fontsize=9, color='black', padding=2):
    """
    Adds a value label on top of (or beside, for barh) every bar in every
    bar container on the given axis. Safe to call after any ax.bar() /
    ax.barh() / DataFrame.plot(kind='bar') call.
    """
    for container in ax.containers:
        # Skip containers that aren't bar containers (e.g. error bars)
        if not isinstance(container, matplotlib.container.BarContainer):
            continue
        labels = [fmt.format(v) if abs(v) > 1e-9 else '' for v in container.datavalues]
        try:
            ax.bar_label(container, labels=labels, fontsize=fontsize,
                         color=color, padding=padding)
        except Exception:
            # Older matplotlib without bar_label support — silently skip
            pass
