#!/usr/bin/env ruby

PIT_ITEM = 'www.nicovideo.jp'
TARGET_URI = 'http://seiga.nicovideo.jp/my/manga/favorite'
URI_BASE = 'http://seiga.nicovideo.jp'

require 'bundler/setup'
Bundler.require
require 'rss/maker'

def main
  config = Pitcgi.get( PIT_ITEM, :require => {
    'mail' => 'mail address or phone number',
    'password' => 'password',
    'token' => 'auto' } )
  nico = Niconico.new( :mail => config[ 'mail' ], :password => config[ 'password' ], :token => config[ 'token' ] )
  nico.login
  config[ 'token' ] = nico.token
  Pitcgi.set( PIT_ITEM, :data => config )

  page = nico.agent.get( TARGET_URI )
  page.search( 'li.unread' ).each do |data|
    item = {}
    title_item = data.at( '.title a' )
    next unless title_item
    item[ :title ] = title_item.text
    item[ :link ] = URI_BASE + data.at( '.latest_episode a' )[ 'href' ]
    thumbnail = data.at( '.content_icon img' )
#    thumbnail[ 'style' ] = 'float: left;' 
    thumbnail[ 'align' ] = 'left' 
    item[ :body ] = thumbnail.to_s
    date_new = data.at( '.date' ).text
    item[ :body ] += date_new + '<br>'
    bookmark = data.at( '.bookmark_link' )
    bookmark[ 'href' ] = URI_BASE + bookmark[ 'href' ]
    item[ :body ] += bookmark.to_s + '<br>'
    item[ :body ] += data.at( '.latest_episode' ).text + '<br>'

    item[ :body ].gsub!( /^[ \t]*/, '' ).gsub!( /[\r\n]*/, '' )
=begin
print "-----\n"
print item[ :body ] + "\n"
=end
    @feed_items << item
  end
end

@feed_items = []
begin
  main
rescue
  data = {}
  data[ :id ] = Time.now.strftime( '%Y%m%d%H%M%S' )
  data[ :title ] = $!.to_s
  data[ :time ] = Time.now
  data[ :body ] = $!.to_s
  $!.backtrace.each do |trace|
    data[ :body ] += '<br>'
    data[ :body ] += trace
  end
  @feed_items << data
end

feed = RSS::Maker.make( 'atom' ) do |maker|
  maker.channel.about = 'nicomanga_feed'
  maker.channel.title = 'お気に入りマンガ - ニコニコ静画'
  maker.channel.description = 'ニコニコ静画のお気に入りマンガのフィードです'
  maker.channel.link = 'http://seiga.nicovideo.jp/my/manga/favorite'
  maker.channel.updated = Time.now
  maker.channel.author = 'sanadan'
  @feed_items.each do |data|
    item = maker.items.new_item
    item.id = data[ :id ] if data[ :id ]
    item.link = data[ :link ] if data[ :link ]
    item.title = data[ :title ]
#    item.date = data[ :time ]
    item.date = Time.now
    item.content.content = data[ :body ]
    item.content.type = 'html'
  end
end

print "Content-Type: application/atom+xml; charset=UTF-8\n"
print "\n"
print feed

