from typing import Union

from flask import flash, g, render_template, url_for
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from markupsafe import Markup
from werkzeug.utils import redirect
from werkzeug.wrappers import Response
from wtforms import SelectField, SubmitField

from openatlas import app, logger
from openatlas.database.anthropology import Anthropology
from openatlas.database.connect import Transaction
from openatlas.models.anthropology import SexEstimation
from openatlas.models.entity import Entity
from openatlas.util.util import button, is_authorized, required_group, uc_first


def print_result(entity: Entity) -> str:
    html = 'Ferembach et al. 1979: <span style="font-weight:bold;">N/A</span>'
    calculation = SexEstimation.calculate(entity)
    if calculation is not None:
        html = \
            f'Ferembach et al. 1979: ' \
            f'<span style="font-weight:bold;">{calculation}</span>'
    return Markup(html)


@app.route('/anthropology/index/<int:id_>')
@required_group('readonly')
def anthropology_index(id_: int) -> Union[str, Response]:
    entity = Entity.get_by_id(id_)
    return render_template(
        'anthropology/index.html',
        entity=entity,
        result=print_result(entity),
        crumbs=[entity, _('anthropological analyzes')])


@app.route('/anthropology/sex/<int:id_>')
@required_group('readonly')
def anthropology_sex(id_: int) -> Union[str, Response]:
    entity = Entity.get_by_id(id_, types=True)
    buttons = []
    if is_authorized('contributor'):
        buttons.append(
            button(
                _('edit'),
                url_for('anthropology_sex_update', id_=entity.id)))
    data = []
    for item in SexEstimation.get_types(entity):
        type_ = g.types[item['id']]
        feature = SexEstimation.features[type_.name]
        data.append({
            'name': type_.name,
            'category': feature['category'],
            'feature_value': feature['value'],
            'option_value': SexEstimation.options[item['description']],
            'value': item['description']})
    return render_template(
        'anthropology/sex.html',
        entity=entity,
        buttons=buttons,
        data=data,
        result=print_result(entity),
        crumbs=[
            entity,
            [_('anthropological analyzes'),
             url_for('anthropology_index', id_=entity.id)],
            _('sex estimation')])


@app.route('/anthropology/sex/update/<int:id_>', methods=['POST', 'GET'])
@required_group('contributor')
def anthropology_sex_update(id_: int) -> Union[str, Response]:

    class Form(FlaskForm):
        pass

    entity = Entity.get_by_id(id_, types=True)
    choices = [(option, option) for option in SexEstimation.options]
    for feature, values in SexEstimation.features.items():
        description = ''
        if values['female'] or values['male']:
            description = f"Female: {values['female']}, male: {values['male']}"
        setattr(
            Form,
            feature,
            SelectField(
                f"{uc_first(feature.replace('_', ' '))} ({values['category']})",
                choices=choices,
                default='Not preserved',
                description=description))
    setattr(Form, 'save', SubmitField(_('save')))
    form = Form()
    types = Anthropology.get_types(entity.id)
    if form.validate_on_submit():
        data = form.data
        data.pop('save', None)
        data.pop('csrf_token', None)
        try:
            Transaction.begin()
            SexEstimation.save(entity, data, types)
            Transaction.commit()
        except Exception as e:  # pragma: no cover
            Transaction.rollback()
            logger.log('error', 'database', 'transaction failed', e)
            flash(_('error transaction'), 'error')
        return redirect(url_for('anthropology_sex', id_=entity.id))

    # Fill in data
    for dict_ in types:
        getattr(form, g.types[dict_['id']].name).data = dict_['description']

    return render_template(
        'anthropology/sex_update.html',
        entity=entity,
        form=form,
        crumbs=[
            entity,
            [_('anthropological analyzes'),
             url_for('anthropology_index', id_=entity.id)],
            [_('sex estimation'), url_for('anthropology_sex', id_=entity.id)],
            _('edit')])
