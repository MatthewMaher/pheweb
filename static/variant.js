
console.log(window.variant);
window.variant.phenos = _.sortBy(window.variant.phenos, function(d) { return Number.parseFloat(d.phewas_code); })
console.log(window.variant);

function create_phewas_plot() {
    var svg_width = $('#phewas_plot_container').width();
    var svg_height = 500;

    var plot_margin = {
        'left': 70,
        'right': 30,
        'top': 10,
        'bottom': 170,
    };

    var plot_width = svg_width - plot_margin.left - plot_margin.right;
    var plot_height = svg_height - plot_margin.top - plot_margin.bottom;


    var x_scale = d3.scale.linear()
        .domain([0, window.variant.phenos.length])
        .range([0, plot_width]);

    var neglog10_min_pval = -Math.log10(d3.min(window.variant.phenos, function(d) {
        return d.pval;
    }));
    var y_scale = d3.scale.linear()
        .domain([neglog10_min_pval, 0])
        .range([0, plot_height]);

    var unique_categories = d3.set(window.variant.phenos.map(function(cat) {
        return cat.category_name;
    })).values();
    var color_by_category = d3.scale.category20()
        .domain(unique_categories);

    var phewas_svg = d3.select('#phewas_plot_container').append("svg")
        .attr('id', 'phewas_svg')
        .attr("width", svg_width)
        .attr("height", svg_height)
        .style("display", "block")
        .style("margin", "auto");
    var phewas_plot = phewas_svg.append("g")
        .attr('id', 'phewas_plot')
        .attr("transform", fmt("translate({0},{1})", plot_margin.left, plot_margin.top));

    // Significance Threshold line
    var significance_threshold = 3e-5;
    var significance_threshold_tooltip = d3.tip()
        .attr('class', 'd3-tip')
        .html(function(d) {
            return 'Significance Threshold: 3E-5';
        })
        .offset([-8,0]);
    phewas_svg.call(significance_threshold_tooltip);

    phewas_plot.append('line')
        .attr('x1', 0)
        .attr('x2', plot_width)
        .attr('y1', y_scale(-Math.log10(significance_threshold)))
        .attr('y2', y_scale(-Math.log10(significance_threshold)))
        .attr('stroke-width', 4)
        .attr('stroke', 'gray')
        .on('mouseover', significance_threshold_tooltip.show)
        .on('mouseout', significance_threshold_tooltip.hide);

    // Points & labels
    var tooltip_template = _.template($('#tooltip-template').html());
    var point_tooltip = d3.tip()
        .attr('class', 'd3-tip')
        .html(function(d) {
            return tooltip_template({d: d, color_by_category: color_by_category});
        })
        .offset([-8,0]);
    phewas_svg.call(point_tooltip);

    var links = phewas_plot.selectAll('a.pheno_point')
        .data(window.variant.phenos)
        .enter()
        .append('a')
        .attr('class', 'pheno_point');
    links.append('circle')
        .attr('cx', function(d, i) {
            return x_scale(i);
        })
        .attr('cy', function(d) {
            return y_scale(-Math.log10(d.pval));
        })
        .attr('r', 3)
        .style('fill', function(d) {
            return color_by_category(d.category_name);
        })
        .on('mouseover', function(d) {
            //Note: once a tooltip has been explicitly placed once, it must be explicitly placed forever after.
            point_tooltip.show(d, this);
        })
        .on('mouseout', point_tooltip.hide);
    links
        .each(function(d,i) {
            d.myIndex = i;
            d.myCircle = this.firstChild;
        })
        .filter(function(d) {
            return d.pval < significance_threshold;
        })
        .append('text')
        .style('text-anchor', 'start')
        .attr('x', function(d) {
            return x_scale(d.myIndex) + 10;
        })
        .attr('y', function(d) {
            return y_scale(-Math.log10(d.pval));
        })
        .attr('dy', '.3em') // vertically center
        .text(function(d) {
            return d.phewas_string.length > 40 ? d.phewas_string.slice(0,30).trim()+'...' : d.phewas_string;
        })
        .on('mouseover', function(d) {
            point_tooltip.show(d, d.myCircle);
        })
        .on('mouseout', point_tooltip.hide);


    // Axes
    var yAxis = d3.svg.axis()
        .scale(y_scale)
        .orient("left");
    phewas_plot.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    phewas_svg.append('text')
        .style('text-anchor', 'middle')
        .attr('transform', fmt('translate({0},{1})rotate(-90)',
                               plot_margin.left*.4,
                               plot_height/2 + plot_margin.top))
        .text('-log10(pvalue)');

    var xAxis = d3.svg.axis()
        .scale(x_scale)
        .orient("bottom")
        .ticks(0);
    phewas_plot.append("g")
        .attr("class", "x axis")
        .attr("transform", fmt("translate(0,{0})", plot_height))
        .call(xAxis);

    phewas_svg.selectAll('text.category_name')
        .data(first_of_each_category())
        .enter() // Do we need this?
        .append('text')
        .style('text-anchor', 'start')
        .attr('transform', function(d) {
            return fmt('translate({0},{1})rotate(50)',
                       plot_margin.left + x_scale(d.myIndex) + 3,
                       plot_height + plot_margin.top + 15);
        })
        .text(function(d) {
            return d.category_name;
        })
        .style('fill', function(d) {
            return color_by_category(d.category_name);
        });

}

$(create_phewas_plot);

function fmt(format) {
    var args = Array.prototype.slice.call(arguments, 1);
    return format.replace(/{(\d+)}/g, function(match, number) {
        return (typeof args[number] != 'undefined') ? args[number] : match;
    });
}

function first_of_each_category() {
    var categories_seen = {};
    return window.variant.phenos.filter(function(pheno) {
        if (categories_seen.hasOwnProperty(pheno.category_name)) {
            return false;
        } else {
            categories_seen[pheno.category_name] = 1;
            return true;
        }
    });
}

console.log(first_of_each_category());