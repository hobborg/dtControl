$(document).ready(function () {
        $('#lastResultsToggle').change(function () {
            changeNotLastRunVisibility(!$(this).prop('checked'));
        });

        function changeNotLastRunVisibility(visible) {
            let spinner = $('#spinner');
            let table = $('#table');
            let caption = $('#table > caption');
            table.css('opacity', .3);
            caption.css('opacity', .3);
            spinner.css('display', 'block');
            setTimeout(function () {
                $('.not_last_run').css('display', visible ? 'table-cell' : 'none');
                table.css('opacity', 1);
                caption.css('opacity', 1);
                spinner.css('display', 'none');
            }, 500);
        }

    $('#smallTextToggle').change(function () {
        $('#table').css('font-size', $(this).prop('checked') ? 'smaller' : 'medium');
    });
    }
);
