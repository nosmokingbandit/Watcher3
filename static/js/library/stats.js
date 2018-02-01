window.addEventListener("DOMContentLoaded", function(){
    var body_style = getComputedStyle(document.getElementsByTagName("body")[0]);
    label_color = body_style.color;
    label_size = body_style.fontSize;
    font_family = body_style.fontFamily;

    status_colors = [];

    each(document.querySelectorAll("div#status_colors > span"), function(span){
        status_colors.push(getComputedStyle(span).backgroundColor);
    })

    profile_colors = [];
    each(document.querySelectorAll("div#profile_colors > span"), function(span){
        profile_colors.push(getComputedStyle(span).backgroundColor);
    });

    var get_stats = $.get(url_base + "/ajax/generate_stats")
    .done(function(response){
        render_charts(response)
    })

    window.addEventListener('beforeunload', function(){
        get_stats.abort();
    });
});

function render_charts(stats){
    /* Renders charts of library stats
    stats: JSON object of stats
    Gathers colors from hidden textarea

    */

    Morris.Donut({
        element: document.querySelector("div#chart_status div.chart"),
        data: stats["status"],
        colors: status_colors,
        labelColor: label_color,
        labelSize: label_size
    })

    Morris.Donut({
        element: document.querySelector("div#chart_profiles .chart"),
        data: stats["qualities"],
        colors: profile_colors,
        labelColor: label_color,
        labelSize: label_size
    })

    Morris.Bar({
        element: document.querySelector("div#chart_years .chart"),
        data: stats["years"],
        xkey: "year",
        ykeys: ["value"],
        labels: ["Movies"],
        barColors: label_color,
        lineColors: label_color,
        xLabelAngle: 35,
        grid: true
    })

    Morris.Line({
        element: document.querySelector("div#chart_added .chart"),
        data: stats["added_dates"],
        xkey: "added_date",
        ykeys: ["value"],
        labels: ["Movies Added"],
        lineColors: label_color,
        pointFillColors: label_color,
        pointStrokeColors: label_color,
        xLabels: "month",
        smooth: false
    })

    Morris.Bar({
        element: document.querySelector("div#chart_scores .chart"),
        data: stats["scores"],
        xkey: "score",
        ykeys: ["value"],
        labels: ["Movies"],
        barColors: label_color,
        pointFillColors: label_color,
        pointStrokeColors: label_color
    })

    each(document.querySelectorAll("svg text"), function(svg){
        svg.style.fontFamily = font_family;
    })
    each(document.querySelectorAll("#chart_status svg path, #chart_profiles svg path"), function(svg){
        svg.setAttribute('stroke', 'transparent');
    })
}
