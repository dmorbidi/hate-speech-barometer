/**
 * Amnesty Hate Analyzer — Gutenberg block registration.
 *
 * @package Dmorbidi\HateAnalyzer
 */

import { registerBlockType } from '@wordpress/blocks';
import { useBlockProps }     from '@wordpress/block-editor';
import { __ }                from '@wordpress/i18n';
import metadata              from './block.json';

registerBlockType( metadata.name, {
    edit: Edit,
    save: Save,
} );

/**
 * Editor preview component.
 */
function Edit() {
    const blockProps = useBlockProps( { className: 'aha-editor-preview' } );

    return (
        <div { ...blockProps }>
            <div className="aha-editor-icon">📊</div>
            <p className="aha-editor-label">
                { __( 'Hate Analyzer', 'hate-speech-analyzer' ) }
            </p>
            <p className="aha-editor-description">
                { __(
                    'Visitors will enter a Facebook post URL to analyze hate speech in its comments.',
                    'hate-speech-analyzer'
                ) }
            </p>
        </div>
    );
}

/**
 * Save returns null — block is server-side rendered.
 */
function Save() {
    return null;
}
