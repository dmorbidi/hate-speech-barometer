/**
 * Amnesty Hate Analyzer — Frontend interactive logic.
 *
 * Finds every .aha-block on the page, wires up the URL input
 * and the Analyze button, calls the WP REST endpoint, and
 * renders a Chart.js pie chart + a stats table with the results.
 *
 * @package Dmorbidi\HateAnalyzer
 */

( function () {
    'use strict';

    const CATEGORIES = [
        { key: 'ACCEPTABLE',    label: 'Acceptable',    color: '#22c55e' },
        { key: 'INAPPROPRIATE', label: 'Inappropriate', color: '#eab308' },
        { key: 'OFFENSIVE',     label: 'Offensive',     color: '#f97316' },
        { key: 'VIOLENT',       label: 'Violent',       color: '#ef4444' },
    ];

    /** Initialise every block on the page */
    function init() {
        document.querySelectorAll( '.aha-block' ).forEach( initBlock );
    }

    /** Wire up one block instance */
    function initBlock( block ) {
        const input   = block.querySelector( '.aha-url-input' );
        const button  = block.querySelector( '.aha-submit' );
        const results = block.querySelector( '.aha-results' );
        const error   = block.querySelector( '.aha-error' );
        const loading = block.querySelector( '.aha-loading' );
        const tbody   = block.querySelector( '.aha-table-body' );
        const canvas  = block.querySelector( '.aha-chart' );

        let chartInstance = null;

        button.addEventListener( 'click', async () => {
            const url = input.value.trim();
            if ( ! url ) {
                showError( error, 'Please enter a Facebook post URL.' );
                return;
            }

            setState( { button, results, error, loading }, 'loading' );

            try {
                const data = await analyze( url );
                renderResults( { results, tbody, canvas, error }, data );
                chartInstance = renderChart( canvas, data, chartInstance );
                setState( { button, results, error, loading }, 'done' );
            } catch ( err ) {
                showError( error, err.message );
                setState( { button, results, error, loading }, 'error' );
            }
        } );

        // Allow Enter key in input
        input.addEventListener( 'keydown', ( e ) => {
            if ( e.key === 'Enter' ) button.click();
        } );
    }

    /** Call the WP REST endpoint */
    async function analyze( url ) {
        const { restUrl, nonce } = window.ahaData || {};

        const response = await fetch( restUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-WP-Nonce':   nonce,
            },
            body: JSON.stringify( { url } ),
        } );

        const json = await response.json();

        if ( ! response.ok ) {
            throw new Error( json.message || 'Analysis failed. Please try again.' );
        }

        return json;
    }

    /** Render table rows and update post title */
    function renderResults( { results, tbody, error }, data ) {
        // Post title
        let titleEl = results.querySelector( '.aha-post-title' );
        if ( ! titleEl ) {
            titleEl = document.createElement( 'p' );
            titleEl.className = 'aha-post-title';
            results.insertBefore( titleEl, results.firstChild );
        }
        titleEl.innerHTML = `Analyzing: <strong>${ escHtml( data.post_title || data.post_url ) }</strong>`;

        // Find max impact for bar scaling
        const maxImpact = Math.max( ...data.stats.map( s => s.impatto_totale ) );

        // Table rows
        tbody.innerHTML = '';
        data.stats.forEach( ( row ) => {
            const cat  = CATEGORIES.find( c => c.key === row.categoria ) || { color: '#666', label: row.categoria };
            const slug = row.categoria.toLowerCase();
            const pct  = maxImpact > 0 ? ( row.impatto_totale / maxImpact ) * 100 : 0;

            const tr = document.createElement( 'tr' );
            tr.innerHTML = `
                <td>
                    <span class="aha-badge aha-badge--${ slug }">
                        ${ escHtml( cat.label ) }
                    </span>
                </td>
                <td>${ row.n_commenti }</td>
                <td>
                    <div class="aha-impact-bar-wrap">
                        <div class="aha-impact-bar">
                            <div
                                class="aha-impact-bar-fill"
                                style="width:${ pct }%; background:${ cat.color };"
                            ></div>
                        </div>
                        <span class="aha-impact-value">${ row.impatto_totale.toFixed( 1 ) }</span>
                    </div>
                </td>
                <td>${ row.impatto_medio.toFixed( 2 ) }</td>
            `;
            tbody.appendChild( tr );
        } );
    }

    /** Render or update the Chart.js doughnut chart */
    function renderChart( canvas, data, existing ) {
        if ( existing ) existing.destroy();

        const labels = data.stats.map( s => {
            const cat = CATEGORIES.find( c => c.key === s.categoria );
            return cat ? cat.label : s.categoria;
        } );
        const values = data.stats.map( s => s.impatto_totale );
        const colors = data.stats.map( s => {
            const cat = CATEGORIES.find( c => c.key === s.categoria );
            return cat ? cat.color : '#666';
        } );

        return new Chart( canvas, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [ {
                    data:            values,
                    backgroundColor: colors,
                    borderColor:     '#000',
                    borderWidth:     3,
                    hoverOffset:     8,
                } ],
            },
            options: {
                responsive:       true,
                cutout:           '55%',
                plugins: {
                    legend: {
                        position:   'bottom',
                        labels: {
                            color:      '#fff',
                            padding:    16,
                            font:       { size: 12 },
                            boxWidth:   14,
                            boxHeight:  14,
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: ( ctx ) => {
                                const total = ctx.dataset.data.reduce( ( a, b ) => a + b, 0 );
                                const pct   = total > 0 ? ( ( ctx.parsed / total ) * 100 ).toFixed( 1 ) : 0;
                                return ` ${ ctx.label }: ${ ctx.parsed.toFixed( 1 ) } (${ pct }%)`;
                            },
                        },
                    },
                },
            },
        } );
    }

    /** UI state machine */
    function setState( { button, results, error, loading }, state ) {
        loading.classList.toggle('is-visible', state === 'loading');
        button.disabled = state === 'loading';

        if ( state === 'done' ) {
            results.hidden = false;
            error.hidden   = true;
        }
        if ( state === 'error' ) {
            results.hidden = true;
        }
        if ( state === 'loading' ) {
            error.hidden = true;
        }
    }

    function showError( el, msg ) {
        el.textContent = msg;
        el.hidden = false;
    }

    function escHtml( str ) {
        return String( str )
            .replace( /&/g, '&amp;' )
            .replace( /</g, '&lt;' )
            .replace( />/g, '&gt;' )
            .replace( /"/g, '&quot;' );
    }

    // Boot
    if ( document.readyState === 'loading' ) {
        document.addEventListener( 'DOMContentLoaded', init );
    } else {
        init();
    }
} )();
