from typing import Optional, Union

from flask import flash, g, render_template, request, url_for
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from werkzeug.wrappers import Response
from wtforms import BooleanField, SelectField, SelectMultipleField, widgets
from wtforms.validators import InputRequired

from openatlas import app
from openatlas.api.import_scripts.vocabs import (
    fetch_top_concept_details, fetch_vocabulary_details, get_vocabularies,
    import_vocabs_data)
from openatlas.database.connect import Transaction
from openatlas.display.tab import Tab
from openatlas.display.table import Table
from openatlas.display.util import (
    button, display_form, display_info, is_authorized, link, required_group)
from openatlas.forms.field import SubmitField
from openatlas.forms.form import get_vocabs_form
from openatlas.models.settings import Settings
from openatlas.models.type import Type


@app.route('/vocabs')
@required_group('readonly')
def vocabs_index() -> str:
    return render_template(
        'tabs.html',
        tabs={'info': Tab(
            'info',
            display_info({
                _('base URL'): g.settings['vocabs_base_url'],
                _('endpoint'): g.settings['vocabs_endpoint'],
                _('user'): g.settings['vocabs_user']}),
            buttons=[
                button(_('edit'), url_for('vocabs_update'))
                if is_authorized('manager') else '',
                button(_('show vocabularies'), url_for('show_vocabularies'))
            ])},
        crumbs=[
            [_('admin'), f"{url_for('admin_index')}#tab-data"],
            'VOCABS'])


@app.route('/vocabs/update', methods=['GET', 'POST'])
@required_group('manager')
def vocabs_update() -> Union[str, Response]:
    form = get_vocabs_form()
    if form.validate_on_submit():
        Settings.update({
            'vocabs_base_url': form.base_url.data,
            'vocabs_endpoint': form.endpoint.data,
            'vocabs_user': form.vocabs_user.data})
        flash(_('info update'), 'info')
        return redirect(url_for('vocabs_index'))
    if request.method != 'POST':
        form.base_url.data = g.settings['vocabs_base_url']
        form.endpoint.data = g.settings['vocabs_endpoint']
        form.vocabs_user.data = g.settings['vocabs_user']
    return render_template(
        'content.html',
        title='VOCABS',
        content=display_form(form),
        crumbs=[
            [_('admin'), f"{url_for('admin_index')}#tab-data"],
            ['VOCABS', f"{url_for('vocabs_index')}"],
            _('edit')])


@app.route('/vocabs/vocabularies')
@required_group('manager')
def show_vocabularies() -> str:
    table = Table(
        header=[_('name'), 'ID', _('default language'), _('languages')])
    for entry in get_vocabularies():
        table.rows.append([
            link(entry['title'], entry['conceptUri'], external=True),
            entry['id'],
            entry['defaultLanguage'],
            ' '.join(entry['languages']),
            vocabulary_detail(
                url_for('vocabulary_import_view', id_=entry['id']))])
    tabs = {'vocabularies': Tab(_('vocabularies'), table=table)}
    return render_template(
        'tabs.html',
        tabs=tabs,
        title='VOCABS',
        crumbs=[
            [_('admin'), f"{url_for('admin_index')}#tab-data"],
            ['VOCABS', f"{url_for('vocabs_index')}"],
            _('vocabularies')])


def vocabulary_detail(url: str) -> Optional[str]:
    return link(_('import'), url) if is_authorized('manager') else None


@app.route('/vocabs/import/<id_>', methods=['GET', 'POST'])
@required_group('manager')
def vocabulary_import_view(id_: str) -> Union[str, Response]:
    details = fetch_vocabulary_details(id_)

    class ImportVocabsHierarchyForm(FlaskForm):
        concepts = SelectMultipleField(
            _('top concepts'),
            render_kw={'disabled': True},
            choices=fetch_top_concept_details(id_),
            option_widget=widgets.CheckboxInput(),
            widget=widgets.ListWidget(prefix_label=False))
        classes = SelectMultipleField(
            _('classes'),
            render_kw={'disabled': True},
            description=_('tooltip hierarchy forms'),
            choices=Type.get_class_choices(),
            option_widget=widgets.CheckboxInput(),
            widget=widgets.ListWidget(prefix_label=False))
        multiple = BooleanField(
            _('multiple'),
            description=_('tooltip hierarchy multiple'))
        language = SelectField(
            _('language'),
            choices=[(lang, lang) for lang in details['languages']],
            default=details['defaultLanguage'])
        confirm_import = BooleanField(
            _("I'm sure to import this hierarchy"),
            default=False,
            validators=[InputRequired()])
        save = SubmitField(_('import hierarchy'))

    form = ImportVocabsHierarchyForm()

    if form.validate_on_submit() and form.confirm_import.data:
        form_data = {
            'top_concepts': form.concepts.data,
            'classes': form.classes.data,
            'multiple': form.multiple.data,
            'language': form.language.data}
        try:
            results = import_vocabs_data(id_, form_data, details)
            count = len(results[0])
            Transaction.commit()
            g.logger.log('info', 'import', f'import: {count} top concepts')
            for duplicate in results[1]:
                g.logger.log(
                    'notice',
                    'import',
                    f'Did not import {duplicate["label"]}, duplicate.')
            import_str = f"{_('import of')}: {count} {_('top concepts')}"
            if results[1]:
                import_str += f'. {_("Check log for not imported concepts")}'
            flash(import_str, 'info')
        except Exception as e:  # pragma: no cover
            Transaction.rollback()
            g.logger.log('error', 'import', 'import failed', e)
            flash(_('error transaction'), 'error')
        return redirect(f"{url_for('type_index')}#menu-tab-custom")
    return render_template(
        'tabs.html',
        tabs={'info': Tab(
            'info',
            _('You are about to import following hierarchy') + ' :' +
            link(details['title'], details['conceptUri'], external=True),
            form=form)},
        title=id_,
        crumbs=[
            [_('admin'), f"{url_for('admin_index')}#tab-data"],
            ['VOCABS', f"{url_for('vocabs_index')}"],
            [_('vocabularies'), f"{url_for('show_vocabularies')}"],
            details['title']])
