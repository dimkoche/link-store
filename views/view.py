import json

import web

import config
from models.source import SourceFactory
from models.article import ArticleFactory, UserArticle
from models.user import login
from models.service import save_opml


t_globals = dict(
    datestr=web.datestr,
    str=str,
    sort=sorted,
    ctx=web.web_session
)
render = web.template.render('templates/', cache=config.cache, globals=t_globals)
render._keywords['globals']['render'] = render

SOURCE_LIST_URL = '/source/list'
HOME_SCREEN = '/article/list/unread/1'


def get_user():
    user_id = web.web_session.user_id
    if not user_id:
        raise web.seeother('/login')
    return user_id


class Index:
    def GET(self):
        return render.base()


class SourceList:
    def list(self):
        user_id = get_user()
        s = SourceFactory()
        l = s.list(user_id)
        return render.source.list(l)

    def GET(self):
        return render.app(self.list())


class SourceAdd:
    def GET(self):
        raise web.seeother(SOURCE_LIST_URL)

    def POST(self):
        user_id = get_user()
        data = web.input()
        url = data.addSourceUrl
        title = data.addSourceTitle or ''
        s_type = data.addSourceType
        sf = SourceFactory()
        sf.add_to_user(user_id, s_type, url, title, config.default_source_category)
        raise web.seeother(SOURCE_LIST_URL)


class SourceDelete:
    def GET(self, source_id):
        user_id = get_user()
        s = SourceFactory()
        s.delete_user_source(int(source_id), int(user_id))
        raise web.seeother(SOURCE_LIST_URL)


class SourceDisable:
    def GET(self, source_id):
        user_id = get_user()
        s = SourceFactory()
        s.disable(int(source_id), user_id)
        raise web.seeother(SOURCE_LIST_URL)


class SourceEnable:
    def GET(self, source_id):
        user_id = get_user()
        s = SourceFactory()
        s.enable(int(source_id), user_id)
        raise web.seeother(SOURCE_LIST_URL)


class ServiceLoadNews:
    def GET(self):
        s = SourceFactory()
        s.load_news()
        raise web.seeother(HOME_SCREEN)


class ServiceImportOpml:
    def load_window(self):
        return render.service.import_opml_form()

    def GET(self):
        return render.app(self.load_window())

    def POST(self):
        user_id = get_user()
        data = web.input()
        if 'opml' in data.keys():
            opml = data.opml
            save_opml(user_id, opml)
            return render.app('OPML saved.')

        return render.app(self.load_window())


class ArticleRead:
    def POST(self):
        user_id = get_user()
        data = web.input()
        article_id = data.article_id
        if not article_id:
            json.dumps({'success': False})
        ua = UserArticle(user_id=user_id, article_id=article_id)
        return json.dumps({'success': ua.read()})

    def GET(self):
        return json.dumps({'success': True})


class ArticleList:
    def list(self, mode, page, user_id):
        page = int(page)
        n = ArticleFactory()
        lst, count = n.list(mode, page, user_id)
        paginate = True
        if mode == 'unread':
            paginate = False
        return render.article.list(lst, page, count, paginate)

    def GET(self, mode, page):
        user_id = get_user()
        page = self.list(mode, page, user_id)
        return render.app(page)


class ArticleLike:
    def POST(self):
        user_id = get_user()
        data = web.input()
        article_id = data.article_id
        if not article_id:
            json.dumps({'success': False})
        ua = UserArticle(user_id=user_id, article_id=article_id)
        return json.dumps({'success': ua.like()})


class ArticleDislike:
    def POST(self):
        user_id = get_user()
        data = web.input()
        article_id = data.article_id
        if not article_id:
            json.dumps({'success': False})
        ua = UserArticle(user_id=user_id, article_id=article_id)
        return json.dumps({'success': ua.dislike()})


class ArticleAdd():
    def GET(self):
        user_id = get_user()
        data = web.input()
        url = data.u
        referrer = data.r
        #time = data.t
        if not url:
            return False

        article_id = ArticleFactory().add(url, user_id, location_type='browser', location=referrer)
        return json.dumps({'success': True, 'article_id': article_id})


class Login():
    def GET(self):
        data = web.input()
        if 'u' in data.keys():
            user = login(data.u)
            if user:
                web.web_session.user_id = user['id']
                web.web_session.username = user['name']
        else:
            web.web_session.user_id = 1
            web.web_session.username = 'Test'
        raise web.seeother(HOME_SCREEN)


class Logout():
    def GET(self):
        web.web_session.user_id = 0
        web.web_session.kill()
        raise web.seeother('/')
