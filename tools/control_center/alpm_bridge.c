// SPDX-License-Identifier: GPL-2.0-only
/* Narrow libalpm ABI bridge. Never a setuid binary or command interpreter.
 * Own implementation from installed alpm.h declarations, not copied code.
 * Root/db/hook paths come only from the fixed privileged Python factory.
 */
#include <alpm.h>
#include <stdlib.h>
#include <string.h>

struct gs_alpm { alpm_handle_t *handle; int locked; };

void *gs_alpm_open(const char *root, const char *dbpath)
{
    alpm_errno_t error;
    struct gs_alpm *ctx = calloc(1, sizeof(*ctx));
    if(!ctx) return NULL;
    ctx->handle = alpm_initialize(root, dbpath, &error);
    if(!ctx->handle) { free(ctx); return NULL; }
    /* Clear defaults: the production factory supplies all effective hookdirs;
     * tests supply only a harmless temporary directory, never host hooks. */
    if(alpm_option_set_hookdirs(ctx->handle, NULL) != 0) {
        alpm_release(ctx->handle); free(ctx); return NULL;
    }
    return ctx;
}

int gs_alpm_hookdir(void *opaque, const char *path)
{
    struct gs_alpm *ctx = opaque;
    return alpm_option_add_hookdir(ctx->handle, path);
}

int gs_alpm_option(void *opaque, const char *name, const char *value)
{
    struct gs_alpm *ctx = opaque;
    if(strcmp(name, "NoUpgrade") == 0) return alpm_option_add_noupgrade(ctx->handle, value);
    if(strcmp(name, "NoExtract") == 0) return alpm_option_add_noextract(ctx->handle, value);
    if(strcmp(name, "IgnorePkg") == 0) return alpm_option_add_ignorepkg(ctx->handle, value);
    if(strcmp(name, "IgnoreGroup") == 0) return alpm_option_add_ignoregroup(ctx->handle, value);
    if(strcmp(name, "Architecture") == 0) return alpm_option_add_architecture(ctx->handle, value);
    if(strcmp(name, "LogFile") == 0) return alpm_option_set_logfile(ctx->handle, value);
    if(strcmp(name, "CheckSpace") == 0) return alpm_option_set_checkspace(ctx->handle, 1);
    return -1;
}

int gs_alpm_scriptlet(void *opaque, const char *name)
{
    struct gs_alpm *ctx = opaque;
    alpm_pkg_t *pkg = alpm_db_get_pkg(alpm_get_localdb(ctx->handle), name);
    return pkg ? alpm_pkg_has_scriptlet(pkg) : -1;
}

int gs_alpm_lock(void *opaque)
{
    struct gs_alpm *ctx = opaque;
    if(ctx->locked || alpm_trans_init(ctx->handle, 0) != 0) return -1;
    ctx->locked = 1; /* flags=0: keep dependencies, conflicts, backups, hooks and lock */
    return 0;
}

int gs_alpm_add(void *opaque, const char *path)
{
    struct gs_alpm *ctx = opaque;
    alpm_pkg_t *pkg = NULL;
    if(!ctx->locked || alpm_pkg_load(ctx->handle, path, 1, 0, &pkg) != 0) return -1;
    /* Signature level 0 is ONLY for independently reviewed exact SHA256 bytes
     * in a protected root cache; this API is not a public path-based installer. */
    if(alpm_add_pkg(ctx->handle, pkg) != 0) { alpm_pkg_free(pkg); return -1; }
    return 0;
}

int gs_alpm_remove(void *opaque, const char *name)
{
    struct gs_alpm *ctx = opaque;
    alpm_pkg_t *pkg = alpm_db_get_pkg(alpm_get_localdb(ctx->handle), name);
    if(!ctx->locked || !pkg) return -1;
    return alpm_remove_pkg(ctx->handle, pkg);
}

static int run_phase(struct gs_alpm *ctx, int commit)
{
    alpm_list_t *errors = NULL, *row;
    alpm_errno_t error;
    int result;
    if(!ctx->locked) return -1;
    /* libalpm requires a non-NULL address for its typed error list. */
    result = commit ? alpm_trans_commit(ctx->handle, &errors)
                    : alpm_trans_prepare(ctx->handle, &errors);
    error = alpm_errno(ctx->handle);
    for(row = errors; row; row = row->next) {
        switch(error) {
            case ALPM_ERR_UNSATISFIED_DEPS: alpm_depmissing_free(row->data); break;
            case ALPM_ERR_CONFLICTING_DEPS: alpm_conflict_free(row->data); break;
            case ALPM_ERR_FILE_CONFLICTS: alpm_fileconflict_free(row->data); break;
            default: free(row->data); break;
        }
    }
    alpm_list_free(errors);
    return result;
}

int gs_alpm_prepare(void *ctx) { return run_phase(ctx, 0); }
int gs_alpm_commit(void *ctx) { return run_phase(ctx, 1); }
const char *gs_alpm_error(void *opaque)
{
    struct gs_alpm *ctx = opaque;
    return alpm_strerror(alpm_errno(ctx->handle));
}

void *gs_alpm_rows(void *opaque, int kind)
{
    struct gs_alpm *ctx = opaque;
    if(kind == 0) return alpm_db_get_pkgcache(alpm_get_localdb(ctx->handle));
    if(kind == 1) return alpm_trans_get_add(ctx->handle);
    if(kind == 2) return alpm_trans_get_remove(ctx->handle);
    return NULL;
}

void *gs_alpm_next(void *row) { return ((alpm_list_t *)row)->next; }
const char *gs_alpm_name(void *row) { return alpm_pkg_get_name(((alpm_list_t *)row)->data); }
const char *gs_alpm_version(void *row) { return alpm_pkg_get_version(((alpm_list_t *)row)->data); }

int gs_alpm_close(void *opaque)
{
    struct gs_alpm *ctx = opaque;
    int result = 0;
    if(ctx->locked && alpm_trans_release(ctx->handle) != 0) result = -1;
    if(alpm_release(ctx->handle) != 0) result = -1;
    free(ctx);
    return result;
}
