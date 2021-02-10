from . import utils
from .utils import PheWebError
from . import conf

import itertools
from collections import OrderedDict,Counter
import typing as ty


def scientific_int(s:str) -> int:
    '''like int(s) but accepts "1.23e2" == 123'''
    try:
        return int(s)
    except ValueError:
        x = float(s)
        if x.is_integer():
            return int(x)
        raise PheWebError("invalid scientific_int: {!r}".format(s))


null_values = ['', '.', 'NA', 'N/A', 'n/a', 'nan', '-nan', 'NaN', '-NaN', 'null', 'NULL']

default_field = {
    'aliases': [],
    'required': False,
    'type': str,
    'nullable': False,
    'from_assoc_files': True, # if this is False, then the field will not be parsed from input files, because annotation will add it.
}

per_variant_fields = OrderedDict([
    ('chrom', {
        'aliases': ['#CHROM', 'chr'],
        'required': True,
        'tooltip_underscoretemplate': '<b><%= d.chrom %>:<%= d.pos.toLocaleString() %> <%= d.ref %> / <%= d.alt %></b><br>',
        'tooltip_lztemplate': False,
    }),
    ('pos', {
        'aliases': ['BEG', 'BEGIN', 'BP'],
        'required': True,
        'type': scientific_int,
        'range': [0, None],
        'tooltip_underscoretemplate': False,
        'tooltip_lztemplate': False,
    }),
    ('ref', {
        'aliases': ['reference'],
        'required': True,
        'tooltip_underscoretemplate': False,
        'tooltip_lztemplate': False,
    }),
    ('alt', {
        'aliases': ['alternate'],
        'required': True,
        'tooltip_underscoretemplate': False,
        'tooltip_lztemplate': False,
    }),
    ('rsids', {
        'from_assoc_files': False,
        'tooltip_underscoretemplate': '<% _.each(_.filter((d.rsids||"").split(",")), function(rsid) { %>rsid: <%= rsid %><br><% }) %>',
        'tooltip_lztemplate': {'condition': 'rsid', 'template': '<strong>{{rsid}}</strong><br>'},
    }),
    ('nearest_genes', {
        'from_assoc_files': False,
        'tooltip_underscoretemplate': 'nearest gene<%= _.contains(d.nearest_genes, ",")? "s":"" %>: <%= d.nearest_genes %><br>',
        'tooltip_lztemplate': False,
    }),
])

per_assoc_fields = OrderedDict([
    ('pval', {
        'aliases': ['PVALUE', 'P', 'P.VALUE'],
        'required': True,
        'type': float,
        'nullable': True,
        'range': [0, 1],
        'sigfigs': 2,
        'tooltip_lztemplate': {
            'condition': False,
            'template': ('{{#if pvalue}}P-value: <strong>{{pvalue|scinotation}}</strong><br>{{/if}}\n' +
                         '{{#if pval}}P-value: <strong>{{pval|scinotation}}</strong><br>{{/if}}'),
        },
        'display': 'P-value',
    }),
    ('beta', {
        'type': float,
        'nullable': True,
        'sigfigs': 2,
        'tooltip_underscoretemplate': 'Beta: <%= d.beta %><% if(_.has(d, "sebeta")){ %> (<%= d.sebeta %>)<% } %><br>',
        'tooltip_lztemplate': 'Beta: <strong>{{beta}}</strong>{{#if sebeta}} ({{sebeta}}){{/if}}<br>',
        'display': 'Beta',
    }),
    ('sebeta', {
        'aliases': ['se'],
        'type': float,
        'nullable': True,
        'sigfigs': 2,
        'tooltip_underscoretemplate': False,
        'tooltip_lztemplate': False,
    }),
    ('or', {
        'type': float,
        'nullable': True,
        'range': [0, None],
        'sigfigs': 2,
        'display': 'Odds Ratio',
    }),
    ('maf', {
        'type': float,
        'range': [0, 0.5],
        'sigfigs': 2,
        'tooltip_lztemplate': {'transform': '|percent'},
        'display': 'MAF',
    }),
    ('af', {
        'aliases': ['A1FREQ', 'FRQ'],
        'type': float,
        'range': [0, 1],
        'proportion_sigfigs': 2,
        'tooltip_lztemplate': {'transform': '|percent'},
        'display': 'AF',
    }),
    ('ac', {
        'type': float,
        'range': [0, None],
        'decimals': 1,
        'display': 'AC',
    }),
    ('r2', {
        'type': float,
        'proportion_sigfigs': 2,
        'nullable': True,
        'display': 'R2',
    }),
    ('tstat', {
        'type': float,
        'sigfigs': 2,
        'nullable': True,
        'display': 'Tstat',
    }),
])

per_pheno_fields = OrderedDict([
    ('num_cases', {
        'aliases': ['NS.CASE', 'N_cases'],
        'type': int,
        'nullable': True,
        'range': [0, None],
        'display': '#cases',
    }),
    ('num_controls', {
        'aliases': ['NS.CTRL', 'N_controls'],
        'type': int,
        'nullable': True,
        'range': [0, None],
        'display': '#controls',
    }),
    ('num_samples', {
        'aliases': ['NS', 'N'],
        'type': int,
        'nullable': True,
        'range': [0, None],
        'display': '#samples',
    }),
    # TODO: phenocode, phenostring, category, &c?
    # TODO: include `assoc_files` with {never_send: True}?
])

fields = dict(itertools.chain(
    per_variant_fields.items(),
    per_assoc_fields.items(),
    per_pheno_fields.items()))

class Field:
    def __init__(self, d):
        self._d = d

    def parse(self, value):
        '''parse from input file'''
        # nullable
        if self._d['nullable'] and value in null_values:
            return ''
        # type
        x = self._d['type'](value)
        # range
        if 'range' in self._d:
            assert self._d['range'][0] is None or x >= self._d['range'][0]
            assert self._d['range'][1] is None or x <= self._d['range'][1]
        if 'sigfigs' in self._d:
            x = utils.round_sig(x, self._d['sigfigs'])
        if 'proportion_sigfigs' in self._d:
            if 0 <= x < 0.5:
                x = utils.round_sig(x, self._d['proportion_sigfigs'])
            elif 0.5 <= x <= 1:
                x = 1 - utils.round_sig(1-x, self._d['proportion_sigfigs'])
            else:
                raise utils.PheWebError('cannot use proportion_sigfigs on a number outside [0-1]')
        if 'decimals' in self._d:
            x = round(x, self._d['decimals'])
        return x
    def read(self, value):
        '''read from internal file'''
        if self._d['nullable'] and value == '':
            return ''  # TODO: should this be None?
        return self._d['type'](value)

# make all aliases lowercase and add parsers
parser_for_field: ty.Dict[str,ty.Callable[[str],ty.Any]] = {}
reader_for_field: ty.Dict[str,ty.Callable[[str],ty.Any]] = {}
for field_name, field_dict in fields.items():
    for k,v in default_field.items():
        field_dict.setdefault(k, v)
    field_dict['aliases'] = list(set([field_name.lower()] + [alias.lower() for alias in field_dict['aliases']]))  # type: ignore
    field_dict['_obj'] = obj = Field(field_dict)
    parser_for_field[field_name] = field_dict['_parse'] = obj.parse
    reader_for_field[field_name] = field_dict['_read'] = obj.read


_alias_counts = Counter(alias for fd in fields.values() for alias in fd['aliases'])  # type: ignore
_repeated_aliases = [alias for alias,count in _alias_counts.most_common() if count > 1]
if _repeated_aliases:
    raise PheWebError('The following aliases appear for multiple fields: {}'.format(_repeated_aliases))


def get_tooltip_underscoretemplate():
    template = ''
    for fieldname, field in fields.items():
        ust = field.get('tooltip_underscoretemplate', None)
        if ust is False:
            continue
        elif ust is None:
            template += '<% if(_.has(d, ' + repr(fieldname) + ')) { %>' + field.get('display', fieldname) + ': <%= d[' + repr(fieldname) + '] %><br><% } %>\n'
        else:
            template += '<% if(_.has(d, ' + repr(fieldname) + ')) { %>' + ust + '<% } %>\n'
    return template
tooltip_underscoretemplate = get_tooltip_underscoretemplate()

def get_tooltip_lztemplate():
    template = ''
    for fieldname, field in fields.items():
        lzt = field.get('tooltip_lztemplate', {})
        if lzt is False:
            continue
        if isinstance(lzt, str):
            lzt = {'template': lzt}
        if 'template' not in lzt:
            lzt['template'] = field.get('display', fieldname) + ': <strong>{{' + fieldname + lzt.get('transform','') + '}}</strong><br>'
        if 'condition' not in lzt:
            lzt['condition'] = fieldname

        if lzt['condition']:
            template += '{{#if ' + lzt['condition'] + '}}' + lzt['template'] + '{{/if}}\n'
        else:
            template += lzt['template'] + '\n'
    return template
tooltip_lztemplate = get_tooltip_lztemplate()