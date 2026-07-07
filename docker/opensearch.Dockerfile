FROM opensearchproject/opensearch:2

ENV DISABLE_SECURITY_PLUGIN=true
ENV discovery.type="single-node"
ENV ES_JAVA_OPTS="-Xms1g -Xmx1g"

HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --start-interval=2s CMD ["/elasticsearch-healthcheck.sh"]

# allow "anonymous_user" to show up without authz
#COPY docker/files/elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml
# ... and allow the unauthenticated anonymous_user to fetch the healthcheck
#COPY docker/files/elasticsearch-roles.yml /usr/share/elasticsearch/config/roles.yml

#COPY --chmod=0755 docker/files/start-elasticsearch.sh /
COPY --chmod=0755 docker/files/elasticsearch-healthcheck.sh /

#ENTRYPOINT ["/start-elasticsearch.sh"]
