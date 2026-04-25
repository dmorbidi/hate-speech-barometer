<?php
/**
 * REST API endpoint for hate analysis.
 *
 * @package Dmorbidi\HateAnalyzer
 */

declare( strict_types=1 );

namespace Dmorbidi\HateAnalyzer;

/**
 * Registers and handles the /hate-speech-analyzer/v1/analyze endpoint.
 */
class Rest_Api {

    private const NAMESPACE = 'hate-speech-analyzer/v1';
    private const ROUTE     = '/analyze';

    public function __construct() {
        add_action( 'rest_api_init', [ $this, 'register_routes' ] );
    }

    public function register_routes(): void {
        register_rest_route( self::NAMESPACE, self::ROUTE, [
            'methods'             => \WP_REST_Server::CREATABLE,
            'callback'            => [ $this, 'handle_analyze' ],
            'permission_callback' => [ $this, 'check_permission' ],
            'args'                => [
                'url' => [
                    'required'          => true,
                    'type'              => 'string',
                    'format'            => 'uri',
                    'sanitize_callback' => 'esc_url_raw',
                    'validate_callback' => [ $this, 'validate_facebook_url' ],
                ],
            ],
        ] );
    }

    /**
     * Only logged-in users (or adjust to public if needed).
     */
    public function check_permission(): bool {
        return true; // Open for demo; restrict with is_user_logged_in() in production.
    }

    /**
     * Validate that the URL is a Facebook post URL.
     */
    public function validate_facebook_url( string $url ): bool {
        return (bool) preg_match( '#^https?://(www\.)?facebook\.com/.+/posts/.+#', $url );
    }

    /**
     * Run the Python analysis pipeline and return JSON results.
     *
     * @param \WP_REST_Request $request Incoming request.
     * @return \WP_REST_Response|\WP_Error
     */
    public function handle_analyze( \WP_REST_Request $request ) {
        $url        = $request->get_param( 'url' );
        $script     = HSA_SCRIPTS_DIR . 'analyze.py';

        if ( ! file_exists( $script ) ) {
            return new \WP_Error(
                'script_missing',
                __( 'Analysis script not found.', 'hate-speech-analyzer' ),
                [ 'status' => 500 ]
            );
        }

        $escaped_url = escapeshellarg( $url );
        $cmd         = "python3 {$script} {$escaped_url} 2>&1";

        // phpcs:ignore WordPress.PHP.DiscouragedPHPFunctions.system_calls_exec
        exec( $cmd, $output, $exit_code );

        if ( $exit_code !== 0 ) {
            return new \WP_Error(
                'script_error',
                implode( "\n", $output ),
                [ 'status' => 500 ]
            );
        }

        $json = json_decode( implode( '', $output ), true );

        if ( json_last_error() !== JSON_ERROR_NONE ) {
            return new \WP_Error(
                'invalid_output',
                __( 'The analysis script returned invalid JSON.', 'hate-speech-analyzer' ),
                [ 'status' => 500 ]
            );
        }

        return rest_ensure_response( $json );
    }
}

new Rest_Api();
