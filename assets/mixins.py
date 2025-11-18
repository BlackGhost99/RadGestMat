"""
Mixins for assets views
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from radgestmat.exceptions import DepartmentAccessDenied
from users.permissions import can_view_department, can_manage_department


class DepartmentMixin:
    """
    Mixin to handle department filtering and permissions
    """
    def get_departement(self):
        """Get department from request"""
        return getattr(self.request, 'departement', None)
    
    def get_queryset(self):
        """Filter queryset by department"""
        queryset = super().get_queryset()
        departement = self.get_departement()
        
        if departement:
            # Filter by department
            queryset = queryset.filter(departement=departement)
        
        return queryset
    
    def check_permissions(self):
        """Check if user has access to department"""
        departement = self.get_departement()
        if not can_view_department(self.request.user, departement):
            raise DepartmentAccessDenied("Vous n'avez pas accès à ce département.")


class PaginationMixin:
    """
    Mixin to add pagination
    """
    paginate_by = 20
    paginate_orphans = 2


class SearchMixin:
    """
    Mixin to add search functionality
    """
    search_fields = []
    search_param = 'q'
    
    def get_search_query(self):
        """Get search query from request"""
        return self.request.GET.get(self.search_param, '').strip()
    
    def get_queryset(self):
        """Add search filtering to queryset"""
        queryset = super().get_queryset()
        search_query = self.get_search_query()
        
        if search_query and self.search_fields:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(q_objects)
        
        return queryset


class FilterMixin:
    """
    Mixin to add filtering functionality
    """
    filter_fields = {}
    
    def get_queryset(self):
        """Add filters to queryset"""
        queryset = super().get_queryset()
        
        for param, field in self.filter_fields.items():
            value = self.request.GET.get(param)
            if value:
                queryset = queryset.filter(**{field: value})
        
        return queryset

