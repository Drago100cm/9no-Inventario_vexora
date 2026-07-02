// static/js/busqueda_global.js

class BusquedaGlobal {
    constructor(options = {}) {
        this.defaultOptions = {
            selector: '.tabla-busqueda-global',
            inputSelector: '.input-busqueda-global',
            noResultsText: 'No se encontraron resultados',
            searchDelay: 300,
            highlightResults: true,
            highlightClass: 'resultado-destacado',
            excludeColumns: [],
            caseSensitive: false,
            searchInHeaders: false,
            minSearchLength: 0
        };

        this.options = { ...this.defaultOptions, ...options };
        this.timeout = null;
        this.currentSearch = '';
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        document.addEventListener('input', this.debounce((e) => {
            if (e.target.matches(this.options.inputSelector)) {
                this.handleSearch(e.target);
            }
        }, this.options.searchDelay));

        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.target.matches(this.options.inputSelector)) {
                e.preventDefault();
                this.handleSearch(e.target);
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && e.target.matches(this.options.inputSelector)) {
                this.limpiarBusqueda(e.target);
                e.target.blur();
            }
        });
    }

    debounce(func, wait) {
        return (...args) => {
            clearTimeout(this.timeout);
            this.timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    handleSearch(input) {
        const searchTerm = (input.value || '').trim();
        this.currentSearch = searchTerm;
        
        if (searchTerm.length < this.options.minSearchLength && searchTerm.length > 0) {
            return;
        }

        const tabla = this.findTable(input);
        if (!tabla) {
            return;
        }

        this.buscarEnTabla(tabla, searchTerm);
    }

    findTable(input) {
        const strategies = [
            () => {
                const tablaId = input.getAttribute('data-tabla');
                return tablaId ? document.getElementById(tablaId) : null;
            },
            () => {
                const container = input.closest(this.options.selector);
                return container ? container.querySelector('table') : null;
            },
            () => input.closest('table'),
            () => document.querySelector(this.options.selector)
        ];

        for (const strategy of strategies) {
            const tabla = strategy();
            if (tabla) return tabla;
        }

        return null;
    }

    buscarEnTabla(tabla, searchTerm) {
        const tbody = tabla.querySelector('tbody');
        if (!tbody) return;

        const term = this.options.caseSensitive ? searchTerm : searchTerm.toLowerCase();
        const filas = Array.from(tbody.querySelectorAll('tr:not(.fila-sin-resultados)'));

        this.limpiarResultadosAnteriores(tbody);
        
        if (this.options.highlightResults) {
            this.removerDestacados(tabla);
        }

        if (!searchTerm) {
            this.mostrarTodasFilas(filas);
            return;
        }

        this.procesarBusqueda(filas, term, tabla);
    }

    limpiarResultadosAnteriores(tbody) {
        const filasMensaje = tbody.querySelectorAll('.fila-sin-resultados');
        filasMensaje.forEach(fila => fila.remove());
    }

    removerDestacados(tabla) {
        const destacados = tabla.querySelectorAll(`.${this.options.highlightClass}`);
        destacados.forEach(elemento => {
            elemento.classList.remove(this.options.highlightClass);
            if (elemento.hasAttribute('data-original-html')) {
                elemento.innerHTML = elemento.getAttribute('data-original-html');
                elemento.removeAttribute('data-original-html');
            }
        });
    }

    mostrarTodasFilas(filas) {
        filas.forEach(fila => {
            fila.style.display = '';
        });
    }

    procesarBusqueda(filas, term, tabla) {
        let resultadosEncontrados = 0;

        filas.forEach(fila => {
            const celdas = this.obtenerCeldasBusqueda(fila);
            let encontrado = false;

            for (const celda of celdas) {
                if (this.buscarEnCelda(celda, term)) {
                    encontrado = true;
                    if (this.options.highlightResults && term) {
                        this.destacarResultado(celda, term);
                    }
                }
            }

            if (encontrado) {
                fila.style.display = '';
                resultadosEncontrados++;
            } else {
                fila.style.display = 'none';
            }
        });

        if (term && resultadosEncontrados === 0) {
            this.insertarFilaSinResultados(tabla);
        }
    }

    obtenerCeldasBusqueda(fila) {
        const celdas = Array.from(fila.querySelectorAll('td'));
        
        return celdas.filter((celda, index) => {
            if (this.options.excludeColumns.includes(index)) {
                return false;
            }
            
            if (this.options.excludeColumns.some(className => 
                typeof className === 'string' && celda.classList.contains(className))) {
                return false;
            }

            return true;
        });
    }

    buscarEnCelda(celda, term) {
        if (!term) return true;
        
        let texto = celda.textContent;
        if (!this.options.caseSensitive) {
            texto = texto.toLowerCase();
        }
        
        return texto.includes(term);
    }

    destacarResultado(celda, term) {
        // NO tocar celdas que tengan botones, enlaces, inputs, iconos, etc.
        if (celda.querySelector('button, a, input, select, textarea, i, svg')) {
            return;
        }

        const originalHTML = celda.innerHTML;
        celda.setAttribute('data-original-html', originalHTML);
        
        const regex = new RegExp(this.escapeRegex(term), this.options.caseSensitive ? 'g' : 'gi');
        const nuevoHTML = originalHTML.replace(regex, match => 
            `<span class="${this.options.highlightClass}">${match}</span>`
        );
        
        celda.innerHTML = nuevoHTML;
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    insertarFilaSinResultados(tabla) {
        const tbody = tabla.querySelector('tbody');
        if (!tbody) return;

        const columnas = this.obtenerNumeroColumnas(tabla);

        const filaMensaje = document.createElement('tr');
        filaMensaje.className = 'fila-sin-resultados';

        const celda = document.createElement('td');
        celda.colSpan = columnas;
        celda.textContent = this.options.noResultsText;

        filaMensaje.appendChild(celda);
        tbody.appendChild(filaMensaje);
    }

    obtenerNumeroColumnas(tabla) {
        const filaThead = tabla.querySelector('thead tr');
        if (filaThead) return filaThead.children.length;

        const primeraFila = tabla.querySelector('tbody tr');
        if (primeraFila) return primeraFila.children.length;

        return 1;
    }

    buscarPorColumnas(tabla, searchTerm, columnIndices = []) {
        if (!tabla) return;
        
        const tbody = tabla.querySelector('tbody');
        if (!tbody) return;

        const term = this.options.caseSensitive ? searchTerm : searchTerm.toLowerCase();
        const filas = Array.from(tbody.querySelectorAll('tr:not(.fila-sin-resultados)'));

        this.limpiarResultadosAnteriores(tbody);
        if (this.options.highlightResults) {
            this.removerDestacados(tabla);
        }

        let resultadosEncontrados = 0;

        filas.forEach(fila => {
            const celdas = fila.querySelectorAll('td');
            let encontrado = false;

            if (!term) {
                fila.style.display = '';
                resultadosEncontrados++;
                return;
            }

            const indices = columnIndices.length > 0 ? columnIndices : 
                           Array.from({length: celdas.length}, (_, i) => i);

            for (const index of indices) {
                if (index < celdas.length && this.buscarEnCelda(celdas[index], term)) {
                    encontrado = true;
                    if (this.options.highlightResults && term) {
                        this.destacarResultado(celdas[index], term);
                    }
                    break;
                }
            }

            fila.style.display = encontrado ? '' : 'none';
            if (encontrado) resultadosEncontrados++;
        });

        if (term && resultadosEncontrados === 0) {
            this.insertarFilaSinResultados(tabla);
        }
    }

    limpiarBusqueda(input) {
        if (!input) return;
        
        input.value = '';
        this.currentSearch = '';
        const tabla = this.findTable(input);
        
        if (tabla) {
            this.buscarEnTabla(tabla, '');
            input.focus();
        }
    }

    recargarBusqueda(input) {
        if (input && this.currentSearch) {
            this.handleSearch(input);
        }
    }
}

// Inicialización automática
document.addEventListener('DOMContentLoaded', function() {
    // Config general
    window.busquedaGlobal = new BusquedaGlobal({
        highlightResults: true   // puedes poner false si no quieres resaltado en ningún lado
    });
    
    // Config por tabla usando data-attributes (opcional)
    document.querySelectorAll('[data-busqueda-global]').forEach(tabla => {
        const options = {
            selector: `#${tabla.id}`,
            inputSelector: tabla.getAttribute('data-input-selector') || '.input-busqueda-global',
            noResultsText: tabla.getAttribute('data-no-results') || 'No se encontraron resultados',
            searchDelay: parseInt(tabla.getAttribute('data-delay')) || 300,
            highlightResults: true
        };
        
        new BusquedaGlobal(options);
    });
});

// Helpers
function inicializarBusquedaTabla(tablaId, options = {}) {
    const tabla = document.getElementById(tablaId);
    if (tabla) {
        tabla.classList.add('tabla-busqueda-global');
        return new BusquedaGlobal({ ...options, selector: `#${tablaId}` });
    }
    return null;
}

function crearInputBusqueda(tablaId, placeholder = 'Buscar...') {
    const tabla = document.getElementById(tablaId);
    if (!tabla) return null;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control input-busqueda-global';
    input.placeholder = placeholder;
    input.setAttribute('data-tabla', tablaId);

    tabla.parentElement.insertBefore(input, tabla);
    return input;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BusquedaGlobal, inicializarBusquedaTabla, crearInputBusqueda };
}
