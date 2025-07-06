from Python_scripts.Feature_functions.diagonal_density import (project_onto_diagonal, fit_and_plot_gmm_overlay)

def compute_gmm_widths(id_list, conn, bodypart_x='head_x_norm', bodypart_y='head_y_norm'):
    """
    For each ID in id_list, project onto diagonal and compute GMM width.
    Returns a list of GMM widths.
    """
    widths = []

    for id in id_list:
        projections = project_onto_diagonal(id, conn, bodypart_x, bodypart_y)
        if len(projections) == 0:
            continue
        result = fit_and_plot_gmm_overlay(projections)
        widths.append(result["gmm_width"])

    return widths
