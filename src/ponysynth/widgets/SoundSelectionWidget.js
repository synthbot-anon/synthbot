// Base class for widgets
const { DOMWidgetView } = require('@jupyter-widgets/base');

/**
 * Utility class for handling an svg element. This is meant to hold a
 * chart. The margins on this class are used to bound the rendered data.
 * They are NOT the margins of the whole chart.
 */
class SvgDisplay {
  svg;
  width;
  height;

  /**
   * @param div Container for this svg element.
   * @param size {width, height} of this svg element.
   * @param margin {top, right, bottom, left} margins for data, excluding
   * axis labels.
   */
  constructor(div, size, margin) {
    const { width: svgWidth, height: svgHeight } = size;
    const width = svgWidth - margin.left - margin.right;
    const height = svgHeight - margin.top - margin.bottom;

    this.svg = d3.select(div)
      .append('svg')
      .attr('width', svgWidth)
      .attr('height', svgHeight)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    this.width = width;
    this.height = height;
  }
}

/**
 * Utility class to hold sound data.
 */
class SoundSamples {
  samples;
  rate;
  duration;

  constructor({ samples, rate }) {
    this.samples = samples;
    this.rate = rate;
    this.duration = samples.length / rate;
  }
}

/**
 * Class to render time axis and pcm axis. This keeps track of
 * how to scale values to match data to rendering locations.
 */
class ScaledAxes {
  #display;
  #axisBottom;
  #axisLeft;
  #axisTransformX;
  #axisTransformY;
  scaleX;
  scaleY;

  /**
   * @param display SvgDisplay object
   */
  constructor(display) {
    this.#display = display;
    // display element to represent time axis
    this.#axisBottom = display.svg.append('g');
    // display element to represent pcm axis
    this.#axisLeft = display.svg.append('g');
  }

  /**
   * Adjust scale and axes to match the given sound data.
   * @param sound SoundSamples object.
   */
  setScales(sound) {
    // function to transform time value to x position
    this.scaleX = d3.scaleLinear()
      .domain([0, sound.duration])
      .range([0, this.#display.width]);

    // function to transform pcm value to y position
    this.scaleY = d3.scaleLinear()
      .domain([d3.min(sound.samples), d3.max(sound.samples)])
      .range([this.#display.height, 0]);

    // function to transform the time axis
    this.#axisTransformX = (g) => (
      g.attr('transform', `translate(0,${this.#display.height})`)
        .call(d3.axisBottom(this.scaleX))
    );

    // function to transform the pcm axis
    this.#axisTransformY = (g) => g.call(d3.axisLeft(this.scaleY));

    return this;
  }

  /**
   * @param t d3js transition object
   */
  render(t) {
    this.#axisBottom.transition(t)
      .call(this.#axisTransformX);

    this.#axisLeft.transition(t)
      .call(this.#axisTransformY);
  }
}

/**
 * Class to render a sequence of pcm samples.
 */
class PcmLine {
  #path;
  #samples;
  #line;

  /**
   * @param display SvgDisplay object. Data bounds in the svg are
   * determined by the margins passed to the SvgDisplay object.
   */
  constructor(display) {
    /**
     * Any data that should be rendered needs to be added to this array.
     * Note: datum() retains the input reference. It doesn't make a copy
     * of its input.
     */
    this.#samples = [];
    this.#path = display.svg.append('path');
    this.#path.datum(this.#samples);
  }

  /**
   * Set the data to render.
   *
   * @param sound SoundSamples object
   * @param scaledAxes ScaledAxes object. This is used to determine the
   * position of each sound sample.
   */
  setSound(sound, scaledAxes) {
    // function to transform each sample to a location
    this.#line = d3.line()
      .x((d, i) => scaledAxes.scaleX(i / sound.rate))
      .y((d) => scaledAxes.scaleY(d));

    // remove old samples, push new samples
    const removeLength = this.#samples.length;
    this.#samples.push(...sound.samples);
    this.#samples.splice(0, removeLength);

    return this;
  }

  /**
   * @param t d3js transition object
   */
  render(t) {
    this.#path.transition(t)
      .attr('fill', 'none')
      .attr('stroke', 'steelblue')
      .attr('stroke-width', 1.5)
      .attr('d', this.#line);
  }
}

/**
 * Transparent surface to select a time point and display the current
 * selection.
 */
class TimeSelection {
  #duration;
  #width;
  #marker;
  #cursor;
  #overlay;
  #markerOpacity = 0;
  #cursorOpacity = 0;
  #cursorX;
  #markerX;
  #callbacks = [];

  /**
   * @param display SvgDisplay indicating surface location and size
   * @param sound SoundSamples object currently being displayed
   */
  constructor({ svg, width, height }, { duration }) {
    this.#duration = duration;
    this.#width = width;

    // object to keep track of the last selected location
    this.#marker = svg.append('line')
      .attr('y1', 0)
      .attr('y2', height)
      .style('stroke', 'red')
      .style('stroke-width', 0.5);

    // object to keep track of the current cursor location
    this.#cursor = svg.append('line')
      .attr('y1', 0)
      .attr('y2', height)
      .style('stroke', 'red')
      .style('stroke-width', 0.5);

    // transparent overlay to track mouse events
    this.#overlay = svg.append('rect')
      .style('fill', 'none')
      .style('pointer-events', 'all')
      .attr('width', width)
      .attr('height', height);

    this.#setupInteractivity(this.#overlay);
  }

  /**
   * Internal function to attach mouse event listeners to the overlay.
   *
   * @param overlay target surface for mouse events
   */
  #setupInteractivity = (overlay) => {
    overlay.on('mouseover', (d, i, nodes) => this.#showCursor(nodes[i]))
      .on('mouseout', () => this.#hideCursor())
      .on('mousemove', (d, i, nodes) => this.#moveCursor(nodes[i]))
      .on('click', (d, i, nodes) => this.#select(nodes[i]));
  }

  #moveCursor = (node) => {
    this.#cursorX = d3.mouse(node)[0];
    this.render();
  };

  #showCursor = (node) => {
    this.#cursorX = d3.mouse(node)[0];
    this.#cursorOpacity = 1;
    this.render();
  };

  #hideCursor = () => {
    this.#cursorOpacity = 0.0;
    this.render();
  };

  /**
   * Handle a selection. This renders the selection point as a line and
   * invokes any registered callbacked.
   */
  #select = (node) => {
    const offset = d3.mouse(node)[0];
    const unboundedTime = (offset / this.#width) * this.#duration;
    const selectedTime = Math.min(Math.max(0, unboundedTime), this.#duration);

    this.#markerX = offset;
    // make the last-selection marker visible, if it wasn't already
    this.#markerOpacity = 0.5;
    this.render();

    // invoke any registered callbacks
    this.#callbacks.forEach((f) => f(selectedTime));
  };

  /**
   * Register a callback that's invoked whenever the user makes a
   * selection.
   *
   * @param callback (timeOffset) => {...}
   */
  addCallback(callback) {
    this.#callbacks.push(callback);
  }

  /**
   * Clear the last selection. It's expected that this is called whenever
   * the data being displayed changes such that the last selection becomes
   * invalid.
   *
   * @param sound the new SoundSamples object being displayed
   */
  reset({ duration }) {
    this.#duration = duration;
    this.#cursorOpacity = 0;
    this.#markerOpacity = 0;

    this.render();
  }

  render() {
    this.#cursor.style('opacity', this.#cursorOpacity)
      .attr('x1', this.#cursorX)
      .attr('x2', this.#cursorX);

    this.#marker.style('opacity', this.#markerOpacity)
      .attr('x1', this.#markerX)
      .attr('x2', this.#markerX);
  }
}

/**
 * Transparent surface to show any highlighted time points over the data.
 */
class TimeHighlights {
  #container;
  #marks = [];
  #width;
  #height;

  /**
   * @param display SvgDisplay object
   */
  constructor({ svg, width, height }) {
    this.#container = svg.append('g');
    this.#width = width;
    this.#height = height;
  }

  /**
   * Highlight the specified mark points.
   *
   * @param marks array of time points
   * @param scaledAxes ScaledAxes object to map time to a display offset
   */
  setMarks(marks, scaledAxes) {
    this.#marks = marks.map(scaledAxes.scaleX);
    return this;
  }

  render(t) {
    // enter fn for a d3 join: create any new marks and slide into place
    const createMarks = (enter) => (
      enter.append('line')
        // new marks enter from the right
        .attr('x1', () => this.#width)
        .attr('x2', () => this.#width)
        .attr('y1', 0)
        .attr('y2', this.#height)
        // ... are a transparent gray
        .style('stroke', 'gray')
        .style('stroke-width', 0.5)
        .style('opacity', 0.5)
        .call((slideIntoPlace) => (
          // ... and slide into place
          slideIntoPlace.transition(t)
            .attr('x1', (d) => d)
            .attr('x2', (d) => d)
        ))
    );

    // update fn for a d3 join: slide marks into their new position
    const updateMarks = (update) => (
      update.transition(t)
        .attr('x1', (d) => d)
        .attr('x2', (d) => d)
    );

    // remove fn for a d3 join: remove these immediately
    const removeMarks = (exit) => exit.remove();

    this.#container.selectAll('line')
      .data(this.#marks)
      .join(createMarks, updateMarks, removeMarks);
  }
}

/**
 * Composite rendering class to draw sound samples and select a time
 * point.
 */
class SoundSelection {
  #display;
  #transitTime;
  #axes;
  #path;
  #timeSelection;
  #highlights;

  /**
   * @param display SvgDisplay object
   * @param transitTime time for transition animations to complete
   * @param sound SoundSamples object
   * @param marks array of time points to highlight in the sound samples
   */
  constructor(display, transitTime, sound, marks) {
    this.#display = display;
    this.#transitTime = transitTime;

    // Create the visual objects that make up this composite
    this.#axes = new ScaledAxes(this.#display).setScales(sound);
    this.#path = new PcmLine(this.#display).setSound(sound, this.#axes);
    this.#timeSelection = new TimeSelection(this.#display, sound);
    this.#highlights = new TimeHighlights(this.#display).setMarks(marks, this.#axes);

    // Render all visual objects
    this.#render();
  }

  /**
   * Register a callback for when the user makes a selection.
   *
   * @param callback (timeOffset) => {...}
   */
  addCallback(callback) {
    this.#timeSelection.addCallback(callback);
    return this;
  }

  /**
   * Set time points to highlight in the displayed sound samples.
   *
   * @param marks array of time points
   */
  setMarks(marks) {
    const t = d3.transition().duration(this.#transitTime);
    this.#highlights.setMarks(marks, this.#axes);
    this.#highlights.render(t);
  }

  /**
   * Display a new set of sound samples.
   *
   * @param sound SoundSamples object
   */
  setSound(sound) {
    const t = d3.transition().duration(this.#transitTime);

    // update the axes
    this.#axes.setScales(sound);
    this.#axes.render(t);

    // clear any existing selection
    this.#timeSelection.reset(sound);

    // update the rendered pcm data
    this.#path.setSound(sound, this.#axes);
    this.#path.render(t);
  }

  /**
   * Set how long it takes for transitions animations to complete.
   *
   * @param transitTime time in milliseconds
   */
  setTransitTime(transitTime) {
    this.#transitTime = transitTime;
  }

  /**
   * Internal function to render this view immediately. This is used the
   * the first time this object needs to be rendered.
   */
  #render = () => {
    const t = d3.transition().duration(0);
    this.#axes.render(t);
    this.#path.render(t);
    this.#timeSelection.render();
    this.#highlights.render(t);
  }
}

/**
 * A widget class to render pcm data and select a time point.
 */
class SoundSelectionWidget extends DOMWidgetView {
  render() {
    // container for the widget
    const div = document.createElement('div');

    // grab parameters set from Python
    const size = this.model.get('size');
    const margin = this.model.get('margin');
    const transitTime = this.model.get('transition_time');
    const sound = new SoundSamples(this.model.get('data'));
    const marks = this.model.get('marks');

    // set up the widget element and on-selection callback
    const display = new SvgDisplay(div, size, margin);
    const soundSelection = new SoundSelection(display, transitTime, sound, marks)
      .addCallback((time) => {
        this.model.set('selection', time);
        this.model.save_changes();
      });

    // update the widget whenever the Python side sends new data
    this.model
      .on('change:data', () => {
        const newSound = new SoundSamples(this.model.get('data'));
        soundSelection.setSound(newSound);
      })
      .on('change:marks', () => {
        const newMarks = this.model.get('marks');
        soundSelection.setMarks(newMarks);
      })
      .on('change:transition_time', () => {
        const newTransitTime = this.model.get('transition_time');
        soundSelection.setTransitTime(newTransitTime);
      });

    this.el.appendChild(div);
  }
}

// expose the widget to jupyter
require.undef('SoundSelectionWidget');
define('SoundSelectionWidget', ['@jupyter-widgets/base'], () => {
  return { SoundSelectionWidget };
});
