# -*- coding: utf-8 -*-

import time
import json
import pdb
import traceback
import ast

from datetime import datetime
from django.db.models import Func, F
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token

from iaer.constants import CODE_SUCCESS, FEEDBACK_FOOTER_IMAGE, DIR_FEEDBACK, MSG_NO_CONTENT, \
    MSG_GET_RED_ENVELOPES_SUCCESS, MSG_DELETE_RED_ENVELOPE_SUCCESS, CODE_NO_CONTENT, \
    MSG_204, MSG_ADD_RED_ENVELOPE_SUCCESS, MSG_ADD_IAER_SUCCESS, MSG_DELETE_IAER_SUCCESS, \
    MSG_GET_IAERS_SUCCESS, MSG_GET_CATEGORIES_SUCCESS, MSG_GET_FUND_SUCCESS, MSG_GET_ABOUT_SUCCESS
from iaer.constants import MSG_SEND_FEEDBACK_SUCCESS
from iaer.models import User, RedEnvelope, Iaer, Category, Fund, About
from iaer.serializers.user import FundSerializer
from iaer.serializers.iaer import IaerSerializer
from iaer.serializers.category import CategorySerializer
from iaer.serializers.about import AboutSerializer
from iaer.serializers.red_envelope import RedEnvelopeSerializer
from iaer.utils import json_response, simple_json_response, invalid_token_response, get_user_by_token, save_error_log, \
        CustomModelViewSet, StandardResultsSetPagination, LargeResultsSetPagination


def about_us_view(request):
    '''
    for iaer in Iaer.objects.filter(category = Category.objects.get(name = '小孩尿布').name):
        iaer.category = Category.objects.get(name = '小孩生活用品').name
        iaer.save()
    '''
    return HttpResponse(MSG_NO_CONTENT)


class RedEnvelopeViewSet(CustomModelViewSet):
    queryset = RedEnvelope.objects.all()
    serializer_class = RedEnvelopeSerializer
    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        try:
            token = request.query_params.get('token')
            user = get_user_by_token(token)
            if user:
                total = 0
                queryset = self.get_queryset()
                for rer in queryset:
                    total += int(rer.money)
                response_data = super(RedEnvelopeViewSet, self).list(request, *args, **kwargs).data
                response_data['total'] = total
                return json_response(response_data, CODE_SUCCESS, MSG_GET_RED_ENVELOPES_SUCCESS)
            else:
                return invalid_token_response()
        except Exception as e:
            return save_error_log(request, e)

    def get_queryset(self):
        token = self.request.query_params.get('token')
        user = get_user_by_token(token)
        user_id = self.request.query_params.get('user_id', -1)
        if int(user_id) < 0:
            return super(RedEnvelopeViewSet, self).get_queryset()
        else:
            user_id = User.objects.get(auth_user=user).id
            return super(RedEnvelopeViewSet, self).get_queryset().filter(user_id=user_id)

    def create(self, request, *args, **kwargs):
        try:
            money_from = request.data.get('money_from')
            money = request.data.get('money')
            remark = request.data.get('remark')
            token = request.data.get('token')
            user = get_user_by_token(token)

            if user:
                red_envelope = RedEnvelope()
                red_envelope.user = User.objects.get(auth_user=user)
                red_envelope.money = money
                red_envelope.money_from = money_from
                red_envelope.remark = remark
                red_envelope.created = timezone.now()
                red_envelope.save()
                response = RedEnvelopeSerializer(red_envelope).data
                return json_response(response, CODE_SUCCESS, MSG_ADD_RED_ENVELOPE_SUCCESS)
            else:
                return invalid_token_response()
        except Exception as e:
            return save_error_log(request, e)

    def destroy(self, request, *args, **kwargs):
        try:
            token = request.data.get('token')
            user = get_user_by_token(token)
            if user:
                red_envelope = self.get_object()
                if red_envelope:
                    try:
                        response = super(RedEnvelopeViewSet, self).destroy(request, *args, **kwargs)
                        if response.status_code != status.HTTP_204_NO_CONTENT:
                            red_envelope.id = -1
                    except Exception as e:
                        red_envelope.id = -1
                        save_error_log(request, e)
                    event_json = RedEnvelopeSerializer(red_envelope).data
                    return json_response(event_json, CODE_SUCCESS, MSG_DELETE_RED_ENVELOPE_SUCCESS)
                else:
                    return simple_json_response(CODE_NO_CONTENT, MSG_204)
            else:
                return invalid_token_response()
        except Exception as e:
            return save_error_log(request, e)


class IaerViewSet(CustomModelViewSet):
    serializer_class = IaerSerializer
    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        try:
            token = request.query_params.get('token')
            user = get_user_by_token(token)
            if user:
                year = datetime.now().year
                month = datetime.now().month
                response_data = super(IaerViewSet, self).list(request, *args, **kwargs).data

                income = 0
                expenditure = 0
                for iaer in self.get_queryset():
                    if iaer.money > 0:
                        income += iaer.money
                    else:
                        expenditure -= iaer.money
                response_data['current_income'] = income
                response_data['current_expenditure'] = expenditure

                if int(self.request.query_params.get('top_list_size', 0)) == 0:
                    this_month_income = 0
                    this_month_expenditure = 0
                    for iaer in self.get_queryset().filter(Q(date__year = year) & Q(date__month = month)):
                        if iaer.money > 0:
                            this_month_income += iaer.money
                        else:
                            this_month_expenditure -= iaer.money
                    response_data['this_month_income'] = this_month_income
                    response_data['this_month_expenditure'] = this_month_expenditure

                    this_year_income = 0
                    this_year_expenditure = 0
                    for iaer in self.get_queryset().filter(date__year = year):
                        if iaer.money > 0:
                            this_year_income += iaer.money
                        else:
                            this_year_expenditure -= iaer.money
                    response_data['this_year_income'] = this_year_income
                    response_data['this_year_expenditure'] = this_year_expenditure

                return json_response(response_data, CODE_SUCCESS, MSG_GET_IAERS_SUCCESS)
            else:
                return invalid_token_response()
        except Exception as e:
            return save_error_log(request, e)

    def get_queryset(self):
        token = self.request.query_params.get('token')
        auth_user = get_user_by_token(token)
        user_id = self.request.query_params.get('user_id', -1)
        years =  self.request.query_params.get('years', '')
        months =  self.request.query_params.get('months', '')
        categories =  self.request.query_params.get('categories', '')
        min_money = int(self.request.query_params.get('min_money', 0))
        max_money = int(self.request.query_params.get('max_money', 0))
        top_list_size = int(self.request.query_params.get('top_list_size', 0))

        flag = 0
        if not years or years == '0':
            flag += 1
        if not months or months == '0':
            flag += 2
        if not categories:
            flag += 4

        if int(user_id) < 0:
            # filter delete queryset
            token = self.request.data.get('token')
            auth_user = get_user_by_token(token)
            if auth_user:
                return Iaer.objects.filter(user = User.objects.get(auth_user = auth_user))
            else:
                return Iaer.objects.filter(pk = -1)
        else:
            if not auth_user:
                return Iaer.objects.filter(pk = -1)
            user_id = User.objects.get(auth_user = auth_user).id
            category_names = []

            if top_list_size == 0:
                if categories:
                    category_list = Category.objects.filter(pk__in = ast.literal_eval(categories)) # covert list string to list
                    for category in category_list:
                        category_names.append(category.name)
                # years not filter
                if flag == 1:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__month__in = ast.literal_eval(months)) & \
                                        Q(category__in = category_names))
                # months not filter
                elif flag == 2:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__year__in = ast.literal_eval(years)) & \
                                        Q(category__in = category_names))
                # years and months not filter
                elif flag == 3:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(category__in = category_names))
                # categories not filter
                elif flag == 4:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__year__in = ast.literal_eval(years)) & \
                                        Q(date__month__in = ast.literal_eval(months)))
                # years and categories not filter
                elif flag == 5:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__month__in = ast.literal_eval(months)))
                # months and categories not filter
                elif flag == 6:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__year__in = ast.literal_eval(years)))
                # years, months and categories not filter
                elif flag == 7:
                    queryset = Iaer.objects.filter(user_id = user_id)
                # falg == 0, filter years, months and categories
                else:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__year__in = ast.literal_eval(years)) & \
                                        Q(date__month__in = ast.literal_eval(months)) & \
                                        Q(category__in = category_names))

                if min_money != 0 or max_money != 0:
                    queryset = queryset.annotate(abs_money = Func(F('money'), function='ABS')) \
                            .filter(Q(abs_money__lte = max_money) & Q(abs_money__gte = min_money))
            else:
                # years not filter
                if flag == 1:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__month = months) & \
                                        Q(category = categories))
                # months not filter
                elif flag == 2:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__year = years) & \
                                        Q(category = categories))
                # years and months not filter
                elif flag == 3:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(category = categories))
                # categories not filter
                elif flag == 4:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__year = years) & \
                                        Q(date__month = months))
                # years and categories not filter
                elif flag == 5:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__month = months))
                # months and categories not filter
                elif flag == 6:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__year = years))
                # years, months and categories not filter
                elif flag == 7:
                    queryset = Iaer.objects.filter(user_id = user_id)
                # flag == 0, filter years, months and categories
                else:
                    queryset = Iaer.objects.filter(Q(user_id = user_id) & \
                                        Q(date__year = years) & \
                                        Q(date__month = months) & \
                                        Q(category = categories))


                if min_money != 0:
                    queryset = queryset.annotate(abs_money = Func(F('money'), function='ABS')) \
                            .filter(Q(abs_money__gte = min_money) & Q(money_type = 0)).order_by('money')
                else:
                    queryset = queryset.order_by('money')[:top_list_size]

            return queryset

    def create(self, request, *args, **kwargs):
        try:
            category = request.data.get('category')
            money = request.data.get('money')
            remark = request.data.get('remark')
            token = request.data.get('token')
            date = request.data.get('date')
            auth_user = get_user_by_token(token)

            if auth_user:
                iaer = Iaer()
                iaer.user = User.objects.get(auth_user = auth_user)
                iaer.money = money
                iaer.category = category
                iaer.remark = remark
                iaer.created = timezone.now()
                if int(money) > 0:
                    iaer.money_type = 1
                else:
                    iaer.money_type = 0
                try:
                    iaer.date = datetime.strptime(date, '%Y-%m-%d').date()
                except ValueError:
                    print("date format error: %s" %date)
                iaer.save()
                response = IaerSerializer(iaer).data
                return json_response(response, CODE_SUCCESS, MSG_ADD_IAER_SUCCESS)
            else:
                return invalid_token_response()
        except Exception as e:
            return save_error_log(request, e)

    def destroy(self, request, *args, **kwargs):
        try:
            token = request.data.get('token')
            auth_user = get_user_by_token(token)
            if auth_user:
                iaer = self.get_object()
                if iaer:
                    try:
                        response = super(IaerViewSet, self).destroy(request, *args, **kwargs)
                        print("168: " + str(response.status_code))
                        if response.status_code != status.HTTP_204_NO_CONTENT:
                            iaer.id = -1
                    except Exception as e:
                        iaer.id = -1
                        save_error_log(request, e)
                    event_json = IaerSerializer(iaer).data
                    return json_response(event_json, CODE_SUCCESS, MSG_DELETE_IAER_SUCCESS)
                else:
                    return simple_json_response(CODE_NO_CONTENT, MSG_204)
            else:
                return invalid_token_response()
        except Exception as e:
            return save_error_log(request, e)



class CategoryViewSet(CustomModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = LargeResultsSetPagination

    def list(self, request, *args, **kwargs):
        return json_response(super(CategoryViewSet, self).list(request, *args, **kwargs).data,
                         CODE_SUCCESS, MSG_GET_CATEGORIES_SUCCESS)


class FundViewSet(CustomModelViewSet):
    queryset = Fund.objects.all()
    serializer_class = FundSerializer
    pagination_class = LargeResultsSetPagination

    def list(self, request, *args, **kwargs):
        return json_response(super(FundViewSet, self).list(request, *args, **kwargs).data,
                         CODE_SUCCESS, MSG_GET_FUND_SUCCESS)


class AboutViewSet(CustomModelViewSet):
    serializer_class = AboutSerializer

    def retrieve(self, request, *args, **kwargs):
        if About.objects.all():
            about = About.objects.all().order_by('-pk')[0]
        else:
            about = About()
            about.id = -1
            about.version_name = '1.0'
            about.version_code = 1
            about.category = -1
            about.comment = ''
            about.datetime = timezone.now()
        return json_response(AboutSerializer(about, context={"request": request}).data, CODE_SUCCESS, MSG_GET_ABOUT_SUCCESS)

