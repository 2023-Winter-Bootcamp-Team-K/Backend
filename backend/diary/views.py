from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Diary
from django.http import Http404


class DiaryCreateView(APIView):
    @swagger_auto_schema(operation_id='일기 생성')
    def post(self, request, format=None):
        if request.user.is_authenticated:
            content = request.data.get("content")
            summary = request.data.get("summary")  # GPT에 의해 생성된 요약
            img_url = request.data.get("img_url")  # DALL-E에 의해 생성된 이미지 URL

            # 일기 생성
            diary = Diary.objects.create(
                user=request.user,
                content=content,
                summary=summary,
                img_url=img_url
            )
            return Response({
                "status": "200",
                "message": "일기 생성 성공",
                "diaryId": diary.id
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "401",
                "message": "인증되지 않은 사용자"
            }, status=status.HTTP_401_UNAUTHORIZED)


class DiaryView(APIView):
    def get_object(self, diary_id):
        try:
            return Diary.objects.get(pk=diary_id)
        except Diary.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        operation_id="일기 조회"
    )
    def get(self, request, diary_id, format=None):
        diary = self.get_object(diary_id)
        diary_data = {
            "status": "200",
            "message": "일기 조회 성공",
            "diaryContent": diary.content,
            "created_at": diary.created_at.strftime("%Y-%m-%d"),
            "imageURL": diary.img_url
        }
        return Response(diary_data)


class DiaryListView(APIView):
    @swagger_auto_schema(
        operation_id="일기 전체 조회"
    )
    def get(self, request, format=None):
        diary_list = Diary.objects.all()
        data = [
            {
                "diaryId": str(diary.id),
                "imageURL": diary.img.url,
                "created_at": diary.created_at.strftime("%Y-&m-%d")
            }
            for diary in diary_list
        ]
        response = {
            "status": "200",
            "message": "일기 전체 조회 성공",
            "data": data
        }
        return Response(response)


class DiaryDeleteView(APIView):
    @swagger_auto_schema(
        operation_id="일기 삭제",
    )
    def delete(self, request, pk, format=None):
        try:
            diary = Diary.objects.get(pk=pk)
            diary.delete()
            return Response({"status": "200", "message":"삭제 성공"}, status.HTTP_200_OK)
        except Diary.DoesNotExist:
            return Response({"status": "404", "message":"일기를 찾을 수 없음"},status=status.HTTP_404_NOT_FOUND)
