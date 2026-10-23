"""Versioned, read-only API surface for the RadGestMat mobile client.

Write operations are intentionally not exposed here yet: checkout/checkin need
server-side idempotency and concurrency controls before offline retries are safe.
"""
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from assets.models import Materiel
from assets.api.serializers import MaterielSerializer
from users.permissions import can_view_department


class MobileAccessMixin:
    """Require an active RadGestMat profile and scope data to its department."""

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get_profile(self, request):
        profile = getattr(request, "profil_utilisateur", None)
        if not profile or not profile.actif:
            return None
        return profile

    def get_queryset(self, request):
        profile = self.get_profile(request)
        if not profile:
            return Materiel.objects.none(), None

        queryset = Materiel.objects.select_related(
            "categorie", "categorie__departement", "departement"
        )
        if profile.role != "SUPER_ADMIN":
            queryset = queryset.filter(departement_id=profile.departement_id)
        return queryset, profile


class MobileAssetListView(MobileAccessMixin, APIView):
    """GET /api/v1/mobile/assets/ — paginated inventory delta/full snapshot."""

    def get(self, request):
        queryset, profile = self.get_queryset(request)
        if profile is None:
            return Response(
                {"detail": "Un profil RadGestMat actif est requis."},
                status=status.HTTP_403_FORBIDDEN,
            )

        updated_since_raw = request.query_params.get("updated_since")
        if updated_since_raw:
            updated_since = parse_datetime(updated_since_raw)
            if updated_since is None:
                return Response(
                    {"detail": "updated_since doit être une date ISO-8601 valide."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if updated_since.tzinfo is None:
                from django.utils import timezone
                updated_since = timezone.make_aware(updated_since)
            queryset = queryset.filter(date_modification__gt=updated_since)

        try:
            limit = int(request.query_params.get("limit", "50"))
            offset = int(request.query_params.get("offset", "0"))
        except (TypeError, ValueError):
            return Response(
                {"detail": "limit et offset doivent être des entiers."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if limit < 1 or limit > 100 or offset < 0:
            return Response(
                {"detail": "limit doit être compris entre 1 et 100 et offset >= 0."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total = queryset.count()
        items = queryset.order_by("id")[offset:offset + limit]
        return Response({
            "results": MaterielSerializer(items, many=True, context={"request": request}).data,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": offset + limit if offset + limit < total else None,
            },
            "server_time": __import__("django.utils.timezone", fromlist=["now"]).now().isoformat(),
        })


class MobileAssetDetailView(MobileAccessMixin, APIView):
    """GET /api/v1/mobile/assets/<asset_id>/ — lookup by QR asset identifier."""

    def get(self, request, asset_id):
        queryset, profile = self.get_queryset(request)
        if profile is None:
            return Response(
                {"detail": "Un profil RadGestMat actif est requis."},
                status=status.HTTP_403_FORBIDDEN,
            )
        materiel = queryset.filter(asset_id=asset_id).first()
        if materiel is None:
            # Avoid revealing whether an asset exists in another department.
            return Response(
                {"detail": "Matériel introuvable ou non autorisé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(MaterielSerializer(materiel, context={"request": request}).data)
