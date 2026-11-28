import re

from django.db.models import Q

from .models import Ad, Match

MIN_SCORE = 60

W_CATEGORY = 40
W_BUILDING = 30
W_DATE = 20

WORD_RE = re.compile(r'\w{4,}')


def _words(ad):
    """Набор «основ» слов: берём первые 5 букв, чтобы «наушники» и «наушников» совпадали."""
    text = f'{ad.title} {ad.description}'.lower()
    return {word[:5] for word in WORD_RE.findall(text)}


def _date_points(lost, found):
    delta = (found.event_date - lost.event_date).days
    if delta < 0:
        return 0  # нашли раньше, чем потеряли: маловероятно
    if delta <= 3:
        return W_DATE
    if delta <= 7:
        return 14
    if delta <= 14:
        return 8
    return 0


def calculate_score(lost, found):
    """Оценка похожести пары «потерял / нашёл» от 0 до 100."""
    if lost.category_id != found.category_id:
        return 0

    shared = len(_words(lost) & _words(found))
    if shared == 0:
        return 0  # ни одного общего слова: считаем, что это разные вещи

    score = W_CATEGORY
    if lost.building_id == found.building_id:
        score += W_BUILDING
    score += _date_points(lost, found)
    score += min(shared, 2) * 5
    return score


def update_matches(ad):
    """Пересчитывает совпадения для активного объявления.
    Возвращает список только что созданных Match."""
    if ad.status != Ad.Status.ACTIVE:
        return []

    opposite = Ad.Type.FOUND if ad.type == Ad.Type.LOST else Ad.Type.LOST
    candidates = (Ad.objects
                  .filter(type=opposite, status=Ad.Status.ACTIVE, category_id=ad.category_id)
                  .exclude(author_id=ad.author_id))

    keep_ids = []
    new_matches = []
    for other in candidates:
        lost, found = (ad, other) if ad.type == Ad.Type.LOST else (other, ad)
        score = calculate_score(lost, found)
        if score < MIN_SCORE:
            continue
        match, created = Match.objects.update_or_create(
            lost_ad=lost, found_ad=found, defaults={'score': score})
        keep_ids.append(match.id)
        if created:
            new_matches.append(match)

    # Убираем устаревшие предложения (объявление отредактировали, категория сменилась)
    (Match.objects
     .filter(Q(lost_ad=ad) | Q(found_ad=ad), status=Match.Status.SUGGESTED)
     .exclude(id__in=keep_ids)
     .delete())
    return new_matches