class DateRangePicker {
    constructor(config) {
        this.startInput = document.getElementById(config.startInputId);
        this.endInput = document.getElementById(config.endInputId);
        this.containerStart = document.getElementById(config.containerStartId);
        this.containerEnd = document.getElementById(config.containerEndId);
        this.timeStartInput = document.getElementById(config.timeStartId);
        this.timeEndInput = document.getElementById(config.timeEndId);

        this.MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        this.DAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
        this.today = new Date();
        this.today.setHours(0, 0, 0, 0);

        this.startDate = null;
        this.endDate = null;
        this.startView = { y: this.today.getFullYear(), m: this.today.getMonth() };
        this.endView = { y: this.today.getFullYear(), m: this.today.getMonth() };

        this.init();
    }

    init() {
        if (this.startInput && this.startInput.value) this.parseInput(this.startInput.value, 'start');
        if (this.endInput && this.endInput.value) this.parseInput(this.endInput.value, 'end');

        this.bindEvents();
        this.renderBoth();
    }

    parseInput(val, which) {
        const d = new Date(val);
        if (!isNaN(d)) {
            const dateObj = new Date(d.getFullYear(), d.getMonth(), d.getDate());
            if (which === 'start') {
                this.startDate = dateObj;
                this.startView = { y: d.getFullYear(), m: d.getMonth() };
                this.timeStartInput.value = this.formatTime(d);
            } else {
                this.endDate = dateObj;
                this.endView = { y: d.getFullYear(), m: d.getMonth() };
                this.timeEndInput.value = this.formatTime(d);
            }
        }
    }

    formatTime(d) {
        return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
    }

    pad(n) { return String(n).padStart(2, '0'); }

    bindEvents() {
        this.timeStartInput.addEventListener('change', () => this.syncToInput('start'));
        this.timeEndInput.addEventListener('change', () => this.syncToInput('end'));
    }

    renderCal(container, view, selectedDate, onPick) {
        const y = view.y, m = view.m;
        let h = '<div class="cal-head">';
        h += '<button type="button" class="nav-btn" data-dir="-1">‹</button>';
        h += '<span class="cal-title">' + this.MONTHS[m] + ' ' + y + '</span>';
        h += '<button type="button" class="nav-btn" data-dir="1">›</button>';
        h += '</div><div class="cal-dow">';
        this.DAYS.forEach(d => h += '<span>' + d + '</span>');
        h += '</div><div class="cal-grid">';

        const first = new Date(y, m, 1).getDay();
        const daysInMonth = new Date(y, m + 1, 0).getDate();

        for (let i = 0; i < first; i++) h += '<span class="cal-day empty"></span>';

        for (let d = 1; d <= daysInMonth; d++) {
            const dt = new Date(y, m, d);
            let cls = 'cal-day';
            if (dt.getTime() === this.today.getTime()) cls += ' today';
            if (selectedDate && dt.getTime() === selectedDate.getTime()) cls += ' selected';
            if (this.startDate && this.endDate && dt > this.startDate && dt < this.endDate) cls += ' in-range';

            h += `<span class="${cls}" data-day="${d}">${d}</span>`;
        }
        h += '</div>';
        container.innerHTML = h;

        // Bind nav buttons
        container.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation(); // prevent form submission or other effects
                const dir = parseInt(btn.dataset.dir);
                view.m += dir;
                if (view.m > 11) { view.m = 0; view.y++; }
                if (view.m < 0) { view.m = 11; view.y--; }
                this.renderBoth();
            });
        });

        // Bind day clicks
        container.querySelectorAll('.cal-day:not(.empty)').forEach(cell => {
            cell.addEventListener('click', () => {
                onPick(new Date(y, m, parseInt(cell.dataset.day)));
            });
        });
    }

    renderBoth() {
        this.renderCal(this.containerStart, this.startView, this.startDate, (d) => {
            this.startDate = d;
            this.syncToInput('start');
            this.renderBoth();
        });
        this.renderCal(this.containerEnd, this.endView, this.endDate, (d) => {
            this.endDate = d;
            this.syncToInput('end');
            this.renderBoth();
        });
    }

    syncToInput(which) {
        const d = which === 'start' ? this.startDate : this.endDate;
        const inp = which === 'start' ? this.startInput : this.endInput;
        const timeEl = which === 'start' ? this.timeStartInput : this.timeEndInput;

        if (!d || !inp) return;
        const t = timeEl.value || '00:00';
        inp.value = d.getFullYear() + '-' + this.pad(d.getMonth() + 1) + '-' + this.pad(d.getDate()) + 'T' + t;
    }
}
