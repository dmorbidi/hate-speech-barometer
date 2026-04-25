<?php
/**
 * Plugin Name: Hate Speech Analyzer
 * Plugin URI:  https://github.com/dmorbidi/hate-speech-analyzer
 * Description: Analyzes hate speech in Facebook post comments using AI, designed for the Humanity Theme.
 * Version:     1.0.0
 * Author:      Dario Morbidi
 * Author URI:  https://github.com/dmorbidi
 * License:     GPL-2.0-or-later
 * Text Domain: hate-speech-analyzer
 *
 * @package Dmorbidi\HateAnalyzer
 */

declare( strict_types=1 );

namespace Dmorbidi\HateAnalyzer;

defined( 'ABSPATH' ) || exit;

define( 'HSA_VERSION',     '1.0.0' );
define( 'HSA_PLUGIN_DIR',  plugin_dir_path( __FILE__ ) );
define( 'HSA_PLUGIN_URL',  plugin_dir_url( __FILE__ ) );
define( 'HSA_SCRIPTS_DIR', HSA_PLUGIN_DIR . 'scripts/' );

require_once HSA_PLUGIN_DIR . 'includes/class-rest-api.php';

/**
 * Register the Gutenberg block and enqueue assets.
 */
function register_block(): void {
    register_block_type( HSA_PLUGIN_DIR . 'src/block.json', [
        'render_callback' => __NAMESPACE__ . '\\render_block',
    ] );

    wp_enqueue_style(
        'aha-frontend',
        HSA_PLUGIN_URL . 'assets/css/frontend.css',
        [],
        HSA_VERSION
    );
}
add_action( 'init', __NAMESPACE__ . '\\register_block' );

/**
 * Enqueue frontend JS (only on pages containing the block).
 */
function enqueue_frontend_assets(): void {
    if ( ! is_singular() ) {
        return;
    }

    global $post;
    if ( ! has_block( 'dmorbidi/hate-analyzer', $post ) ) {
        return;
    }

    wp_enqueue_script(
        'chartjs',
        'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js',
        [],
        '4.4.1',
        true
    );

    wp_enqueue_script(
        'aha-frontend',
        HSA_PLUGIN_URL . 'assets/js/frontend.js',
        [ 'chartjs' ],
        HSA_VERSION,
        true
    );

    wp_localize_script( 'aha-frontend', 'ahaData', [
        'restUrl' => rest_url( 'hate-analyzer/v1/analyze' ),
        'nonce'   => wp_create_nonce( 'wp_rest' ),
    ] );
}
add_action( 'wp_enqueue_scripts', __NAMESPACE__ . '\\enqueue_frontend_assets' );

/**
 * Server-side render callback for the block.
 *
 * @param array $attributes Block attributes.
 * @return string Rendered HTML.
 */
function render_block( array $attributes ): string {
    $placeholder = esc_html__( 'Enter a Facebook post URL…', 'hate-speech-analyzer' );
    $button_label = esc_html__( 'Analyze', 'hate-speech-analyzer' );

    return sprintf(
        '<div class="aha-block wp-block-dmorbidi-hate-analyzer" data-nonce="%s">
            <div class="aha-input-row">
                <input
                    class="aha-url-input"
                    type="url"
                    placeholder="%s"
                    aria-label="%s"
                />
                <button class="aha-submit" type="button">%s</button>
            </div>
            <div class="aha-results" hidden>
                <div class="aha-chart-wrapper">
                    <canvas class="aha-chart" aria-label="%s" role="img"></canvas>
                </div>
                <table class="aha-table">
                    <thead>
                        <tr>
                            <th>%s</th>
                            <th>%s</th>
                            <th>%s</th>
                            <th>%s</th>
                        </tr>
                    </thead>
                    <tbody class="aha-table-body"></tbody>
                </table>
            </div>
            <p class="aha-error" hidden></p>
            <div class="aha-loading" hidden>
                <span class="aha-spinner"></span>
                %s
            </div>
        </div>',
        esc_attr( wp_create_nonce( 'wp_rest' ) ),
        $placeholder,
        $placeholder,
        $button_label,
        esc_html__( 'Hate speech distribution pie chart', 'hate-speech-analyzer' ),
        esc_html__( 'Category', 'hate-speech-analyzer' ),
        esc_html__( 'Comments', 'hate-speech-analyzer' ),
        esc_html__( 'Total Impact', 'hate-speech-analyzer' ),
        esc_html__( 'Avg Impact', 'hate-speech-analyzer' ),
        esc_html__( 'Analyzing comments…', 'hate-speech-analyzer' )
    );
}
