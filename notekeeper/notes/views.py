from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Note, AddNoteForm
from django.contrib import messages
import json
from datetime import datetime, timedelta 
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa


def render_to_pdf(template_src, context_dict={}):
    '''
        Helper function to generate pdf from html
    '''
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse("Error Rendering PDF", status=400)


def generate_pdf(request, slug):
    note = get_object_or_404(Note, slug=slug)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    notes = Note.objects.filter(user=request.user).order_by('-updated_at')[:10]
    add_note_form = AddNoteForm()

    context = {
        'notes': notes,
        'note_detail': note,
        'add_note_form': add_note_form,
    }
    pdf = render_to_pdf('note_as_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "note.pdf"
        content = "inline; filename={}".format(filename)
        content = "attachment; filename={}".format(filename)
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Not found")


def home(request):
    notes = Note.objects.filter(user=request.user).order_by('-updated_at')[:10]
    all_notes = Note.objects.filter(user=request.user).order_by('-updated_at')
    paginator = Paginator(all_notes, 15)
    form_error = False
    last_month = datetime.today() - timedelta(days=30)
    last_month_note_count = Note.objects.filter(
            user=request.user,
            created_at__gt=last_month
        ).count()
    
    if request.method == 'POST':
        form = AddNoteForm(request.POST)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.user = request.user
            form_data.save()
            # Without this next line the tags won't be saved.
            form.save_m2m()
            form = AddNoteForm()
            messages.success(request, 'Note added successfully!')
        else:
            form_error = True
    else:
        form = AddNoteForm()
    page = request.GET.get('page')
    all_notes = paginator.get_page(page)
    context = {
        'notes': notes,
        'all_notes': all_notes,
        'add_note_form': form,
        'form_error': form_error,
        'last_month_note_count': last_month_note_count,
    }
    return render(request, 'notes.html', context)


def get_note_details(request, slug):
    note = get_object_or_404(Note, slug=slug)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')

    notes = Note.objects.filter(user=request.user).order_by('-updated_at')[:10]
    add_note_form = AddNoteForm()

    context = {
        'notes': notes,
        'note_detail': note,
        'add_note_form': add_note_form,
    }
    return render(request, 'note_details.html', context)


def edit_note_details(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    if request.method == 'POST':
        form = AddNoteForm(request.POST, instance=note)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.user = request.user
            form_data.save()
            form.save_m2m()
            return redirect('note_detail', slug=note.slug)
    else:
        form = AddNoteForm(initial={
            'note_title': note.note_title,
            'note_content': note.note_content,
            'tags': ','.join([i.slug for i in note.tags.all()]),
        }, instance=note)
        return render(request, 'modals/edit_note_modal.html', {'form': form})


def delete_note(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    note.delete()
    return redirect('notes')


def search_note(request):
    if request.is_ajax():
        q = request.GET.get('term')
        notes = Note.objects.filter(
                note_title__icontains=q,
                user=request.user
            )[:10]
        results = []
        for note in notes:
            note_json = {}
            note_json['slug'] = note.slug
            note_json['label'] = note.note_title
            note_json['value'] = note.note_title
            results.append(note_json)
        data = json.dumps(results)
    else:
        note_json = {}
        note_json['slug'] = None
        note_json['label'] = None
        note_json['value'] = None
        data = json.dumps(note_json)
    return HttpResponse(data)