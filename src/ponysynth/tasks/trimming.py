# a task has visuals & controls, loss metrics, variance metrics
# each task has hypothetical features that are applicable
# an algorithm takes features and produces a candidate solution
# the user visuals & controls enable the user to act as an algorithm
# the difference between the user's choices and the algo determines the loss
# differences in algo outputs determines variance
# samples shown to the user are prioritized based on variance
# the user can see the output of different algorithms
# and decide to discard some techniques, variants of an existing one
# or spawn a new one from a partial specification

# for any sample, the user can choose to set it aside
# or tag it and add a description

# need to measure each algorithms's contribution to variance
# need to measure each feature's contribution to ???
# figure out if variance is decreasing with more information
# goal: variance should go to zero for all samples

# visuals, controls, loss metrics, variance metrics
# features, algorithms, samples 
# high loss on old samples indicates a bad algorithm


class TrimmingTask:

	def metrics(self):
		return []

	def algorithms(self):
		return []

	def loss(self):
		return None

	def variance(self):
		return None

	def controls(self, candidates):
		# draw candidate answers within the visuals
		pass


class AlgoVisuals:
	def historical_error(self, algos):
		pass

	def variance(self, algos, sample):
		pass


class Functor:
	def __init__(self, domain, codomain):
		pass


# enable rotating between different views
# represent display as a functor from focal points to ui elements
class Display:
	def __init__(self):
		super(Display, self).__init__(userfocus, elements)
		self.focus = focus
		self.elements = elements
		# userfocus determines where the focus can be
		# in terms of css style properties (location, color, size, etc)

	def render(self):
		html = '<html>%s</html>'
		javascript = '<script>%s</script>'

		for f in self.focus:
			style = f.style
			element = f.target
		# associate ui elements with focus properties
		# print the html string to draw this

# universe -> universe
# soundtasks -> ui elements
# trimtask -> relevant ui elements



# algorithms relevant to a task
# represent an algo as a morphism (take input, produce output)
# probsolv: represent an algopool as a presheaf (input undefined, output defined)
# explore: or copresheaf? (input defined, output undefined)
# a particular task (input, output defined) is associated with a hom object
# algopool is defined by a partial specification
class AlgoPool:
	pass

# an algorithm is a diagram over features



# track algo statistics
# maybe also user statistics
class MetricsMonitor:
	pass

# what's the relationship between features and algorithms?
#  -> an algorithm produces output of the target type
#  -> a feature produces output of a semantic type

# algorithm vs ensemble?
#  -> an ensemble is an algorithm that
#  -> takes other algortihm outputs as features
#  -> but its agnostic to algorithm output type
#  -> since it uses loss and variance metrics

# user's decision to remove an algorithm
# can be considered a loss metric
# and taking a grad desc step on it results in
# removing the algo

# purpose of a loss metric is just to figure out how to change the algo

class Morphism:
	# TODO: track how useful a feature is
	def __init__(self, domain, codomain, f):
		self.domain = domain
		self.codomain = codomain
		self.f = f

	def __call__(self, **kwargs):
		return f(**kwargs)


class Hom:
	def __init__(self, domain, codomain, params, f):
		pass

class Model:
	# TODO: track model error
	def __init__(self, features, codomain, f):
		self.features = features
		self.codomain = codomain
		self.f = f


class SampleHtml:
	def __init__(self, clipbot):
		self.clipbot = clipbot

	def html(self):
		pass

class AlgoTableHtml:
	def __init__(self, algobot):
		self.algobot = algobot

	def html(self):
		pass

class TrimmingSampleHtml:
	def __init__(self):
		pass

	def html(self):
		pass

class FormWidget:
	def __init__(self):
		pass

class ClipWidget:
	def __init__(self):
		pass


def samples_widget(id, samples, rate, width=920, height=400):
	return f"""
<div id="{id}"></div>
<script>
(function() {{
    var margin = {{top: 10, right: 30, bottom: 30, left: 60}},
        width = {width} - margin.left - margin.right,
        height = {height} - margin.top - margin.bottom;

    svg = d3.select("#{id}")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
            .attr("transform",
                  "translate(" + margin.left + "," + margin.top + ")");

    var x = d3.scaleLinear()
        .domain([0, ponysynth.data.{samples}.length / ponysynth.data.{rate}])
        .range([0, width]);
    svg.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x));

    var y = d3.scaleLinear()
        .domain([d3.min(ponysynth.data.{samples}), d3.max(ponysynth.data.{samples})])
        .range([height, 0]);
    svg.append("g")
        .call(d3.axisLeft(y));

    selection = svg.append("g")
        .append("line")
        .attr("y1", 0).attr("y2", height)
        .style("stroke", "gray")
        .style("stroke-width", 0.5)
        .style("opacity", 0)

    cursor = svg.append("g")
        .append("line")
        .attr("y1", 0).attr("y2", height)
        .style("stroke", "red")
        .style("stroke-width", 0.5)
        .style("opacity", 0)

    svg.append("path")
        .datum(ponysynth.data.{samples})
        .attr("fill", "none")
        .attr("stroke", "steelblue")
        .attr("stroke-width", 1.5)
        .attr("d", d3.line()
             .x(function(d, i) {{i += 1; return x(i / ponysynth.data.{rate})}})
             .y(function(d) {{ return y(d)}}));

    svg.append("rect")
        .style("fill", "none")
        .style("pointer-events", "all")
        .attr("width", width)
        .attr("height", height)
        .on("mouseover", function() {{
            offset = d3.mouse(this)[0];
            cursor.style("opacity", 1)
                .attr("x1", offset)
                .attr("x2", offset)
        }})
        .on("mousemove", function() {{
            offset = d3.mouse(this)[0];
            cursor.attr("x1", offset)
                .attr("x2", offset)
        }})
        .on("mouseout", function() {{
           cursor.style("opacity", 0); 
        }})
        .on("click", function() {{
            var offset = d3.mouse(this)[0];
            selection.style("opacity", 1.0)
                .attr("x1", offset)
                .attr("x2", offset)
        }});
}})();
</script>"""

