from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from deep_translator import GoogleTranslator
from app.dependencies import get_current_admin_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translate", tags=["translate"])


class TranslateRequest(BaseModel):
    text: str
    source_lang: str  # uz, ru, en
    target_langs: List[str]  # ["ru", "en"] yoki ["uz", "en"] va h.k.


class TranslateResponse(BaseModel):
    translations: dict  # {"ru": "...", "en": "..."}
    success: bool
    message: Optional[str] = None


# Til kodlari mapping (deep-translator uchun)
LANG_CODES = {
    "uz": "uz",
    "ru": "ru",
    "en": "en"
}

LANGUAGE_NAMES = {
    "uz": "O'zbek tili",
    "ru": "Rus tili",
    "en": "Ingliz tili"
}


def translate_text_google(text: str, source_lang: str, target_lang: str) -> str:
    """Google Translate orqali tarjima qilish (bepul)"""
    try:
        translator = GoogleTranslator(source=LANG_CODES[source_lang], target=LANG_CODES[target_lang])
        result = translator.translate(text)
        return result if result else text
    except Exception as e:
        logger.error(f"Google Translate xatoligi: {str(e)}")
        raise e


@router.post("/", response_model=TranslateResponse)
async def translate_text(
    data: TranslateRequest,
    current_user = Depends(get_current_admin_user)
):
    """
    Matnni bir tildan boshqa tillarga tarjima qilish.
    Google Translate (bepul) ishlatiladi.
    """
    if not data.text or not data.text.strip():
        return TranslateResponse(
            translations={},
            success=False,
            message="Tarjima qilish uchun matn kiritilmagan"
        )

    if data.source_lang not in LANG_CODES:
        raise HTTPException(status_code=400, detail=f"Noto'g'ri manba tili: {data.source_lang}")

    for lang in data.target_langs:
        if lang not in LANG_CODES:
            raise HTTPException(status_code=400, detail=f"Noto'g'ri maqsad tili: {lang}")

    try:
        translations = {}

        for target_lang in data.target_langs:
            if target_lang == data.source_lang:
                translations[target_lang] = data.text
                continue

            translated = translate_text_google(data.text, data.source_lang, target_lang)
            translations[target_lang] = translated

            logger.info(f"Tarjima: {data.source_lang} -> {target_lang}, uzunlik: {len(data.text)} -> {len(translated)}")

        return TranslateResponse(
            translations=translations,
            success=True,
            message="Muvaffaqiyatli tarjima qilindi"
        )

    except Exception as e:
        logger.error(f"Tarjima xatoligi: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Tarjima qilishda xatolik: {str(e)}"
        )


@router.post("/batch", response_model=TranslateResponse)
async def translate_batch(
    texts: dict,  # {"name": "Loyiha nomi", "description": "Tavsif"}
    source_lang: str,
    target_langs: List[str],
    current_user = Depends(get_current_admin_user)
):
    """
    Bir nechta matnni bir vaqtda tarjima qilish.
    """
    if not texts:
        return TranslateResponse(
            translations={},
            success=False,
            message="Tarjima qilish uchun matnlar kiritilmagan"
        )

    try:
        all_translations = {}

        for target_lang in target_langs:
            if target_lang == source_lang:
                all_translations[target_lang] = texts
                continue

            translated_dict = {}
            for key, value in texts.items():
                if value and value.strip():
                    translated_dict[key] = translate_text_google(value, source_lang, target_lang)
                else:
                    translated_dict[key] = value

            all_translations[target_lang] = translated_dict

        return TranslateResponse(
            translations=all_translations,
            success=True,
            message="Muvaffaqiyatli tarjima qilindi"
        )

    except Exception as e:
        logger.error(f"Batch tarjima xatoligi: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Tarjima qilishda xatolik: {str(e)}"
        )
