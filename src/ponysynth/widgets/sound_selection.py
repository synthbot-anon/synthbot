from traitlets import Unicode, List, Float, Int, validate, default, TraitError, Tuple, Dict
from ipywidgets import DOMWidget, register
from IPython import display as ipd
from ponysynth import widgets


@register
class SoundSelectionWidget(DOMWidget):
    _view_name = Unicode('SoundSelectionWidget').tag(sync=True)
    _view_module = Unicode('SoundSelectionWidget').tag(sync=True)
    _view_module_version = Unicode('0.1.0').tag(sync=True)

    data = Dict({'samples': List(), 'rate': Int()}).tag(sync=True)
    size = Dict({'width': Int(), 'height': Int()}).tag(sync=True)
    margin = Dict({
        'top': Int(),
        'right': Int(),
        'bottom': Int(),
        'left': Int()
    }).tag(sync=True)
    transition_time = Int().tag(sync=True)

    marks = List().tag(sync=True)
    selection = Float().tag(sync=True)

    @validate('data')
    def _valid_data(self, proposal):
        data = proposal['value']

        if len(data['samples']) == 0:
            raise TraitError('List of samples cannot be empty')
        if data['rate'] <= 0:
            raise TraitError('Sampling rate must be greater than 0')

        return proposal['value']

    @validate('size')
    def _valid_size(self, proposal):
        size = proposal['value']

        if size['width'] <= 0:
            raise TraitError('Width must be greater than 0')
        if size['height'] <= 0:
            raise TraitError('Height must be greater than 0')

        return proposal['value']

    @default('size')
    def _default_size(self):
        return {'width': 460, 'height': 140}

    @default('margin')
    def _default_margin(self):
        return {'top': 10, 'right': 30, 'bottom': 30, 'left': 60}

    @default('transition_time')
    def _default_transition_time(self):
        return 500


widgets.load_js('SoundSamplesWidget.js')
